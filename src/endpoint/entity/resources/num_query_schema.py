from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.validation_errors import NonZeroUIntSearchFieldError


import re


class NumberQuerySchema:
    allowed_number_fields = {
        "FileSize": EntityModel.FileSize,
        "Duration": EntityModel.Duration,
        "ImageWidth": EntityModel.ImageWidth,
        "ImageHeight": EntityModel.ImageHeight,

    }
    is_float = {
        "Duration": True,
    }
    pattern = re.compile(r"^(Min|Max)$")

    def __init__(self, num_field, **kwargs):
        self.num_field = num_field
        self.matching_map = {
            key: value for key, value in kwargs.items() if key.startswith(num_field)
        }

    @staticmethod
    def validate(field, matching_keys):
        if len(matching_keys) > 2:
            return False
        if len(matching_keys) == 0 or len(matching_keys) == 1:
            return True
        # IF two keys are provided they must be Min and Max
        min_key = next((k for k in matching_keys if k.endswith("Min")), None)
        max_key = next((k for k in matching_keys if k.endswith("Max")), None)

        if not min_key or not max_key:
            return False

        return True

    def translate(self):
        if hasattr(self, "translatedMap"):
            return

        matching_keys = self.matching_map.keys()
        if not self.validate(self.num_field, matching_keys):
            raise Exception("Validation Failed")

        translatedMap = {}
        for key in self.matching_map.keys():
            prefix_len = len(self.num_field)
            suffix = key[prefix_len:]
            if not suffix:
                translatedMap[key] = self.translate_to_num(
                    self.matching_map[key],
                    key,
                    nulSupported=True,
                    is_float=self.is_float.get(self.num_field, False),
                )
                continue
            m1 = self.pattern.fullmatch(suffix)
            if m1:
                translatedMap[key] = self.translate_to_num(
                    self.matching_map[key],
                    key,
                    nulSupported=False,
                    is_float=self.is_float.get(self.num_field, False),
                )
                continue

            raise Exception(f"Invalid argument {key}={self.matching_map[key]}")
        self.translatedMap = translatedMap
        return self.translatedMap

    def translate_to_num(self, value, attr, nulSupported: bool, is_float: bool):
        if isinstance(value, list):
            if len(value) == 1 and value[0] in ("__null__", "__notnull__"):
                if nulSupported:
                    return value[0]
                else:
                    # Specific error for unsupported __null__/__notnull__
                    raise NonZeroUIntSearchFieldError(
                        attr, value[0]
                    )  # Point to specific item
            return [
                self.translate_value(v, value, attr, is_float=is_float) for v in value
            ]
        if value in ("__null__", "__notnull__"):
            if nulSupported:
                return value
            else:
                raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code

        return self.translate_value(value, value, attr, is_float=is_float)

    def translate_value(self, v, value, attr, is_float: bool):
        try:
            if is_float:
                translated = float(v)
            else:
                translated = int(v)
                if isinstance(v, float) and float(translated) != v:
                    raise ValueError(f"Cannot convert float {v} to an exact integer.")
        except (ValueError, TypeError):
            raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
        return translated

    def query(
        self,
        value: int | float,
        Min: bool = False,
        Max: bool = False,
    ):
        dbColumn = self.allowed_number_fields[self.num_field]
        num_query_filters = []
        if Min:
            num_query_filters.append(dbColumn >= value)
        elif Max:
            num_query_filters.append(dbColumn <= value)
        else:
            if isinstance(value, list):
                num_query_filters.append(dbColumn.in_(value))
            elif value == "__null__":
                num_query_filters.append(dbColumn.is_(None))
            elif value == "__notnull__":
                num_query_filters.append(dbColumn.is_not(None))
            else:
                num_query_filters.append(dbColumn == value)

        return num_query_filters

    @property
    def queries(self):
        self.translate()
        num_query_filters = []
        for key, value in self.translatedMap.items():
            prefix_len = len(self.num_field)
            suffix = key[prefix_len:]
            if not suffix:
                num_query_filters.extend(self.query(value))
                continue
            m = self.pattern.fullmatch(suffix)
            if m:
                min_max, = m.groups()
                args = dict(
                    Min=(min_max == "Min"),
                    Max=(min_max == "Max"),
                )
                num_query_filters.extend(self.query(value, **args))
                continue
            raise Exception("Invalid numField")

        return num_query_filters
        pass
