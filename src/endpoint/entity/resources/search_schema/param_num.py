from src.endpoint.entity.resources.search_schema.param import Param
from src.utils.custom_errors.internal_server_errors import DataNotLoadedError, UnexpectedFailure


from marshmallow import ValidationError


import re


class NumParam(Param):
    def __init__(
        self, field_name: str, dbColumn, data, no_variant: bool = False, is_null_supported: bool = True,  is_float=False
    ):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant, is_null_supported=is_null_supported)
        self.is_float = is_float
        self.patterns = [re.compile(r"^(Min|Max)$")]

    def load(self) -> bool:
        return super().load(lambda key, value: self.to_float(key, value) if  self.is_float  else self.to_int(key, value))

    def validate(self):
        if not super().validate():
            return False
        if len(self.raw_fields.keys()) > (1 if self.no_variant else 2):
            return self.TooManyParametersUsed()
        if len(self.raw_fields.keys()) == 2:
            min_key = next((k for k in self.raw_fields if k.endswith("Min")), None)
            max_key = next((k for k in self.raw_fields if k.endswith("Max")), None)

            if not min_key or not max_key:
                return self.TooManyParametersUsed(self.raw_fields.keys())
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
                f"use either {self.field_name}, {self.field_name}Min, {self.field_name}Max "
                f"or both {self.field_name}Min and {self.field_name}Max. "
            }
        )

    @property
    def queries(self):
        if not hasattr(self, "fields"):
            raise DataNotLoadedError(f"data is not loaded for {self.field_name}")

        num_query_filters = []
        if len(self.fields) > 0:
            for key, value in self.fields.items():
                prefix_len = len(self.field_name)
                suffix = key[prefix_len:]
                if not suffix:
                    num_query_filters.append(self.query(value))
                    continue
                if not self.no_variant:
                    m = self.patterns[0].fullmatch(suffix)
                    if m:
                        (min_max,) = m.groups()
                        args = dict(
                            Min=(min_max == "Min"),
                            Max=(min_max == "Max"),
                        )
                        num_query_filters.append(self.query(value, **args))
                        continue
                raise UnexpectedFailure()
            
        return num_query_filters