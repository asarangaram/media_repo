from src.endpoint.entity.resources.search_schema.param import Param
from src.utils.custom_errors.internal_server_errors import DataNotLoadedError, UnexpectedFailure


from marshmallow import ValidationError


import re


class StrParam(Param):
    def __init__(self, field_name: str, dbColumn, data, no_variant: bool = False):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.patterns = [re.compile(r"^(StartsWith|Contains)$")]

    def load(self):
        return super().load(lambda key, value: self.to_str(key, value))

    def validate(self):
        if not super().validate():
            return False
        if len(self.raw_fields.keys()) > 1:
            return self.TooManyParametersUsed()
        return True

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
        if not hasattr(self, "fields"):
            raise DataNotLoadedError(f"data is not loaded for {self.field_name}")

        str_query_filters = []
        if len(self.fields) > 0:
            for key, value in self.fields.items():
                prefix_len = len(self.field_name)
                suffix = key[prefix_len:]
                if not suffix:
                    query = self.query(value)
                    str_query_filters.append(query)
                    continue
                if not self.no_variant:
                    if suffix == "StartsWith":
                        str_query_filters.append(self.query(value, startsWith=True))
                        continue
                    elif suffix == "Contains":
                        str_query_filters.append(self.query(value, contains=True))
                        continue
                raise UnexpectedFailure()

        return str_query_filters