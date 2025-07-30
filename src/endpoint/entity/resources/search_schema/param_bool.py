from src.endpoint.entity.resources.search_schema.param import Param
from src.utils.custom_errors.internal_server_errors import DataNotLoadedError, UnexpectedFailure


class BoolParam(Param):
    def __init__(self, field_name: str, dbColumn, data, no_variant: bool = False):
        super().__init__(field_name, dbColumn, data, no_variant=no_variant)
        self.patterns = []

    def load(self):
        return super().load(lambda key, value: self.to_bool(key, value))

    def validate(self):
        if not super().validate():
            return False
        if len(self.raw_fields.keys()) > 1:
            return self.TooManyParametersUsed()
        return True

    def _valid(self):
        return len(self.raw_fields) in [0, 1]

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
                raise UnexpectedFailure()

        return num_query_filters
