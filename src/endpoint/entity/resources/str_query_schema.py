from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.validation_errors import NonZeroUIntSearchFieldError


import re


class StringQuerySchema:
    allowed_string_fields = {
        "label": EntityModel.label,
        "description": EntityModel.description,
         "MIMEType": EntityModel.MIMEType,
        "type": EntityModel.type,
        "extension": EntityModel.extension,
    }
    match_only = {
        "MIMEType": True,
        "type": True,
        "extension": True,
    }
    pattern = re.compile(r"^(StartsWith|Contains)$")

    def __init__(self, str_field, **kwargs):
        self.str_field = str_field
        self.matching_map = {
            key: value for key, value in kwargs.items() if key.startswith(str_field)
        }

    @staticmethod
    def validate(field, matching_keys):
        if len(matching_keys) == 0 or len(matching_keys) == 1:
            return True
        return False

    def translate(self):
        if hasattr(self, "translatedMap"):
            return

        matching_keys = self.matching_map.keys()
        if not self.validate(self.str_field, matching_keys):
            raise Exception("Validation Failed")

        translatedMap = {}
        for key in self.matching_map.keys():
            prefix_len = len(self.str_field)
            suffix = key[prefix_len:]
            if not suffix:
                translatedMap[key] = self.translate_to_str(
                    self.matching_map[key],
                    key,
                    nulSupported=True,
                )
                continue
            if not self.match_only.get(self.str_field, False):
                m1 = self.pattern.fullmatch(suffix)
                if m1:
                    translatedMap[key] = self.translate_to_str(
                        self.matching_map[key],
                        key,
                        nulSupported=False,
                    )
                    continue

            raise Exception(f"Invalid argument {key}={self.matching_map[key]}")
        self.translatedMap = translatedMap
        return self.translatedMap

    def translate_to_str(
        self,
        value,
        attr,
        nulSupported: bool,
    ):
        if isinstance(value, list):
            if len(value) == 1 and value[0] in ("__null__", "__notnull__"):
                if nulSupported:
                    return value[0]
                else:
                    # Specific error for unsupported __null__/__notnull__
                    raise NonZeroUIntSearchFieldError(
                        attr, value[0]
                    )  # Point to specific item
            return [self.translate_value(v, value, attr) for v in value]
        if value in ("__null__", "__notnull__"):
            if nulSupported:
                return value
            else:
                raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code

        return self.translate_value(
            value,
            value,
            attr,
        )

    def translate_value(self, v, value, attr):
        try:
            translated = str(v)
        except (ValueError, TypeError):
            raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
        return translated

    def query(
        self,
        value: int | float,
        startsWith: bool = False,
        contains: bool = False,
    ):
        dbColumn = self.allowed_string_fields[self.str_field]
        str_query_filters = []
        if not self.match_only.get(self.str_field, False):
            if startsWith:
                str_query_filters.append(dbColumn.ilike(f"{value}%"))
            elif contains:
                str_query_filters.append(dbColumn.ilike(f"%{value}%"))
        else:
            if isinstance(value, list):
                str_query_filters.append(dbColumn.in_(value))
            elif value == "__null__":
                str_query_filters.append(dbColumn.is_(None))
            elif value == "__notnull__":
                str_query_filters.append(dbColumn.is_not(None))
            else:
                str_query_filters.append(dbColumn == value)

        return str_query_filters

    @property
    def queries(self):
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
