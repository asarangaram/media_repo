import re
from marshmallow import ValidationError

from clmediakit import fromTimeStamp

from src.utils.custom_errors.internal_server_errors import DataNotLoadedError


class Param:
    def __init__(
        self,
        field_name: str,
        dbColumn,
        data,
        no_variant: bool = False,
        is_null_supported: bool = False,
    ):
        self.field_name = field_name
        self.raw_fields = {
            key: value for key, value in data.items() if key.startswith(field_name)
        }
        self.dbColumn = dbColumn
        self.no_variant = no_variant
        self.is_null_supported = is_null_supported

    def load(self, fn_valid_value):
        self.fields = {}
        if self.validate():
            for key, value in self.raw_fields.items():
                v1 = value[0] if isinstance(value, list) and len(value) == 1 else value
                if isinstance(v1, list):
                    self.fields[key] = [fn_valid_value(key, value) for v in v1]
                elif self.is_null_supported and v1 in ("__null__", "__notnull__"):
                    self.fields[key] = v1
                else:
                    self.fields[key] = fn_valid_value(key, value)
        return self.fields

    def validate(self):
        keys = []
        for key in self.raw_fields.keys():
            prefix_len = len(self.field_name)
            suffix = key[prefix_len:]
            if not suffix:
                keys.append(key)
                continue
            if not self.no_variant:
                for pattern in self.patterns:
                    m = pattern.fullmatch(suffix)
                    if m:
                        keys.append(key)
                        continue
                    else:
                        return self.unknownField(key)
            else:
                return self.unknownField(key)

    def unknownField(self, key):
        raise ValidationError({key: "unknown field"})

    @staticmethod
    def to_int(key, value):
        try:
            if isinstance(value, list):
                return [int(v) for v in value]
            return int(value)
        except (ValueError, TypeError) as error:
            raise ValidationError({key: str(error)})

    @staticmethod
    def to_float(key, value):
        try:
            if isinstance(value, list):
                return [float(v) for v in value]
            return float(value)
        except (ValueError, TypeError) as error:
            raise ValidationError({key: str(error)})

    @staticmethod
    def to_str(key, value):
        try:
            if isinstance(value, list):
                return [str(v) for v in value]
            return str(value)
        except (ValueError, TypeError) as error:
            raise ValidationError({key: str(error)})

    @staticmethod
    def to_datetime(key, value):
        try:
            if isinstance(value, list):
                return [fromTimeStamp((int(v))) for v in value]
            return fromTimeStamp((int(value)))
        except (ValueError, TypeError) as error:
            raise ValidationError({key: str(error)})

    @staticmethod
    def to_bool(key, value):
        intvalue = Param.to_int(key, value)

        if intvalue == 1:
            return True
        elif intvalue == 0:
            return False

        raise ValidationError({key: f"{value} is not valid"})

    def query(
        self,
        value,
        startsWith: bool = False,
        contains: bool = False,
        Min: bool = False,
        Max: bool = False,
    ):
        if not self.no_variant:
            if Min:
                filter = self.dbColumn >= value
            elif Max:
                filter = self.dbColumn <= value
            if startsWith:
                filter = self.dbColumn.ilike(f"{value}%")
            elif contains:
                filter = self.dbColumn.ilike(f"%{value}%")
        else:
            if isinstance(value, list):
                filter = self.dbColumn.in_(value)
            elif value == "__null__":
                filter = self.dbColumn.is_(None)
            elif value == "__notnull__":
                filter = self.dbColumn.is_not(None)
            else:
                filter = self.dbColumn == value

        return filter


class NumParam(Param):
    def __init__(
        self, field_name: str, dbColumn, data, no_variant: bool = False, is_float=False
    ):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.is_float = is_float
        self.patterns = [re.compile(r"^(Min|Max)$")]

    def load(self) -> bool:
        return super().load(lambda key, value: self.to_int(key, value))

    def validate(self):
        super().validate()
        if len(self.raw_fields.keys()) > (1 if self.no_variant else 2):
            return self.TooManyParametersUsed()
        if len(self.raw_fields.keys()) == 2:
            min_key = next((k for k in self.raw_fields if k.endswith("Min")), None)
            max_key = next((k for k in self.raw_fields if k.endswith("Max")), None)

            if not min_key or not max_key:
                return self.TooManyParametersUsed(self.raw_fields.keys())

    def TooManyParametersUsed(self):
        if self.no_variant:
            raise ValidationError(
                {
                    f"{self.raw_fields.keys()}": f"Too many parameters used. {self.field_name}can be used only once"
                }
            )
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "Too many parameters used"
                f"use either {self.field_name}, {self.field_name}Min, {self.field_name}Max "
                f"or both {self.field_name}Min and {self.field_name}Max. "
            }
        )

    @property
    def queries(self):
        if not hasattr("fields"):
            raise DataNotLoadedError(f"data is not loaded for {self.field_name}")

        num_query_filters = []
        for key, value in self.fields.items():
            prefix_len = len(self.field_name)
            suffix = key[prefix_len:]
            if not suffix:
                num_query_filters.append(self.query(value))
                continue
            m = self.patterns[0].fullmatch(suffix)
            if m:
                (min_max,) = m.groups()
                args = dict(
                    Min=(min_max == "Min"),
                    Max=(min_max == "Max"),
                )
                num_query_filters.append(self.query(value, **args))
                continue

        return num_query_filters


class StrParam(Param):
    def __init__(self, field_name: str, dbColumn, data, no_variant: bool = False):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.patterns = [re.compile(r"^(StartsWith|Contains)$")]

    def load(self):
        return super().load(lambda key, value: self.to_str(key, value))

    def validate(self):
        super().validate()
        if len(self.raw_fields.keys()) > 1:
            return self.TooManyParametersUsed()

    def TooManyParametersUsed(self):
        if self.no_variant:
            raise ValidationError(
                {
                    f"{self.raw_fields.keys()}": f"Too many parameters used. {self.field_name}can be used only once"
                }
            )
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "Too many parameters used"
                f"use either {self.field_name}, {self.field_name}STARTWITH, {self.field_name}CONTAINS "
                f"or both {self.field_name}Min and {self.field_name}Max. "
            }
        )

    @property
    def queries(self):
        if not hasattr("fields"):
            raise DataNotLoadedError(f"data is not loaded for {self.field_name}")
        self.translate()
        str_query_filters = []
        for key, value in self.translatedMap.items():
            prefix_len = len(self.str_field)
            suffix = key[prefix_len:]
            if not suffix:
                str_query_filters.extend(self.query(value))
                continue
            if not self.match_only.get(self.str_field, False):
                if suffix == "StartsWith":
                    str_query_filters.extend(self.query(value, startsWith=True))
                    continue
                elif suffix == "Contains":
                    str_query_filters.extend(self.query(value, contains=True))
                    continue
            raise Exception("Invalid strField")

        return str_query_filters


class DateTimeParam(Param):
    def __init__(self, field_name: str, dbColumn, data, no_variant: bool = False):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.patterns = [
            re.compile(r"^(YY(MM(DD)?)?)?(From|Till)$"),
            re.compile(r"^(YY)?(MM)?(DD)?(HH)?$"),
        ]

    def load(self):
        return super().load(lambda key, value: self.to_datetime(key, value))

    def validate(self):
        super().validate()
        if len(self.raw_fields.keys()) > (1 if self.no_variant else 2):
            return self.TooManyParametersUsed()

        if len(self.raw_fields.keys()) == 2:
            from_key = next(
                (k for k in self.raw_fields.keys() if k.endswith("From")), None
            )
            till_key = next(
                (k for k in self.raw_fields.keys() if k.endswith("Till")), None
            )

            if not from_key or not till_key:
                return self.conflictingParametersUsed()

            if from_key[:-4] != till_key[:-4]:
                return self.mismatchInMasks()

        return True

    def mismatchInMasks(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "parameters are conflicting. "
                "masks are not matching between From and Till"
            }
        )

    def conflictingParametersUsed(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "parameters are conflicting. "
                "use either a matching query or a range query with From and Till "
                "when using range query, masks"
            }
        )

    def TooManyParametersUsed(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "Too many parameters used. "
                "use either a matching query or a range query with From and Till"
            }
        )

    def _valid(self):
        match len(self.raw_fields):
            case 0:
                return True
            case 1:
                return True
            case 2:
                from_key = next(
                    (k for k in self.raw_fields if k.endswith("From")), None
                )
                till_key = next(
                    (k for k in self.raw_fields if k.endswith("Till")), None
                )
                if from_key and till_key:
                    suffix_from = from_key[len(self.field_name) : -4]
                    suffix_till = till_key[len(self.field_name) : -4]
                    return suffix_from == suffix_till
                return False
            case _:
                return False


class BoolParam(Param):
    def __init__(self, field_name: str, dbColumn, data, no_variant: bool = False):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.patterns = []

    def load(self):
        return super().load(lambda key, value: self.to_bool(key, value))

    def validate(self):
        super().validate()
        if len(self.raw_fields.keys()) > 1:
            return self.TooManyParametersUsed()

    def _valid(self):
        return len(self.raw_fields) in [0, 1]
