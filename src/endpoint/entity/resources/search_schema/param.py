from marshmallow import ValidationError

from clmediakit import fromTimeStamp


class Param:
    def __init__(
        self,
        field_name: str,
        dbColumn,
        data,
        no_variant: bool,
        is_null_supported: bool,
    ):
        self.field_name = field_name
        self.raw_fields = {
            key: value
            for key, value in data.items()
            if key.startswith(field_name)
        }
        self.dbColumn = dbColumn
        self.no_variant = no_variant
        self.is_null_supported = is_null_supported

    def load(self, fn_valid_value):
        self.fields = {}
        if self.validate() and len(self.raw_fields) > 0:
            for key, value in self.raw_fields.items():
                v1 = (
                    value[0]
                    if isinstance(value, list) and len(value) == 1
                    else value
                )
                if self.is_null_supported and v1 in (
                    "__null__",
                    "__notnull__",
                ):
                    self.fields[key] = v1
                else:
                    self.fields[key] = fn_valid_value(key, v1)
        return self.fields

    def validate(self):
        for key in self.raw_fields.keys():
            prefix_len = len(self.field_name)
            suffix = key[prefix_len:]
            if not suffix:
                continue
            if not self.no_variant:
                mList = [
                    pattern.fullmatch(suffix) for pattern in self.patterns
                ]
                if any(item is not None for item in mList):
                    continue

            return self.unknownField(key)
        return True

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
        except (ValueError, TypeError) as error:  # pragma: no cover
            raise ValidationError({key: str(error)})  # pragma: no cover

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
        if Min:
            filter = self.dbColumn >= value
        elif Max:
            filter = self.dbColumn <= value
        elif startsWith:
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
