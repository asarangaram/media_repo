from datetime import datetime
from typing import Any, Mapping

from marshmallow import ValidationError

from clmediakit import toTimeStamp
from src.endpoint.entity.models import EntityModel

from src.endpoint.entity.resources.search_schema.param_datetime import DateTimeParam
from src.endpoint.entity.resources.search_schema.param_num import NumParam
from src.endpoint.entity.resources.search_schema.param_str import StrParam
from src.endpoint.entity.resources.search_schema.param_bool import (
    BoolParam,
)


class SearchSchema:
    def __init__(self, data: Mapping[str, Any]):
        data_flat = SearchSchema.flatten_dict(data.copy())
        query_parameters = [
            NumParam("FileSize", EntityModel.FileSize, data_flat),
            NumParam("ImageWidth", EntityModel.ImageWidth, data_flat),
            NumParam("ImageHeight", EntityModel.ImageHeight, data_flat),
            NumParam("parentId", EntityModel.parentId, data_flat, no_variant=True),
            NumParam("id", EntityModel.id, data_flat, no_variant=True),
            NumParam("Duration", EntityModel.Duration, data_flat, is_float=True),
            StrParam("label", EntityModel.label, data_flat),
            StrParam("description", EntityModel.description, data_flat),
            StrParam("MIMEType", EntityModel.MIMEType, data_flat, no_variant=True),
            StrParam("type", EntityModel.type, data_flat, no_variant=True),
            StrParam("extension", EntityModel.extension, data_flat, no_variant=True),
            DateTimeParam("addedDate", EntityModel.addedDate, data_flat),
            DateTimeParam("updatedDate", EntityModel.updatedDate, data_flat),
            DateTimeParam("CreateDate", EntityModel.CreateDate, data_flat),
            BoolParam(
                "isCollection", EntityModel.isCollection, data_flat, no_variant=True
            ),
            BoolParam("isDeleted", EntityModel.isDeleted, data_flat, no_variant=True),
        ]
        # Load
        self.query_parameters = []
        self._fields = {}
        for query_parameter in query_parameters:
            fields = query_parameter.load()
            if len(fields) > 0:
                self.query_parameters.append(query_parameter)
                self._fields.update(fields)
        unused_keys = data.keys() - self._fields.keys()
        if len(unused_keys) > 0:
            raise ValidationError({key: "unknown field" for key in unused_keys})

    @property
    def fields(self):
        return SearchSchema.convert(self._fields)

    @property
    def queries(self):
        all_queries = []
        for query_parameter in self.query_parameters:
            all_queries.extend(query_parameter.queries)
        return all_queries

    @staticmethod
    def flatten_dict(data_map):
        try:
            for key in list(data_map.keys()):
                value = data_map[key]

                if isinstance(value, dict):  # recursive
                    data_map[key] = SearchSchema.flatten_dict(value)
                elif isinstance(value, list):
                    if len(value) == 1:
                        data_map[key] = value[0]
                    elif len(value) == 0:
                        del data_map[key]
                if value is None:
                    del data_map[key]

            return data_map
        except Exception:
            raise

    @staticmethod
    def convert(data):
        if isinstance(data, bool):
            return int(data)
        elif isinstance(data, datetime):
            return int(toTimeStamp(data))
        elif isinstance(data, dict):
            return {k: SearchSchema.convert(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [SearchSchema.convert(item) for item in data]
        else:
            return data
