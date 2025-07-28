from flask import request
from marshmallow import ValidationError
from sqlalchemy import func
from sqlalchemy.dialects import sqlite
from sqlalchemy_continuum import version_class
from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources.num_query_schema import NumberQuerySchema
from src.endpoint.entity.resources.datetime_query_schema import DateTimeQuerySchema
from src.endpoint.entity.resources.str_query_schema import StringQuerySchema
from src.endpoint.entity.schema import ItemSchema, ItemsQuerySchema
from src.utils.flatten_dict import convert_bools_to_int_recursive, flatten_dict


class SearchFilters:
    def __init__(self, MediaVersion, **kwargs):
        self.MediaVersion = MediaVersion
        query_args = flatten_dict(request.args.to_dict(flat=False))
        self.parsed_queries_internal = ItemsQuerySchema().load(query_args)

        self.dateQueries = {}
        self.numQueries = {}
        self.strQueries = {}

        known_fields = set(ItemsQuerySchema().fields.keys())
        for date_field in DateTimeQuerySchema.allowed_date_fields.keys():
            self.dateQueries[date_field] = DateTimeQuerySchema(
                date_field, **self.parsed_queries_internal
            )
            translated = self.dateQueries[date_field].translate()
            self.parsed_queries_internal.update(translated)
            known_fields.update(translated.keys())

        for num_field in NumberQuerySchema.allowed_number_fields.keys():
            self.numQueries[num_field] = NumberQuerySchema(
                num_field, **self.parsed_queries_internal
            )
            translated = self.numQueries[num_field].translate()
            self.parsed_queries_internal.update(translated)
            known_fields.update(translated.keys())

        for str_field in StringQuerySchema.allowed_string_fields.keys():
            self.strQueries[str_field] = StringQuerySchema(
                str_field, **self.parsed_queries_internal
            )
            translated = self.strQueries[str_field].translate()
            self.parsed_queries_internal.update(translated)
            known_fields.update(translated.keys())

        unused_keys = self.parsed_queries_internal.keys() - known_fields
        if len(unused_keys) > 0:
            raise ValidationError({key: "unknown field" for key in unused_keys})

    @property
    def parsed_queries(self):
        return convert_bools_to_int_recursive(self.parsed_queries_internal)

    @staticmethod
    def _apply_string_filter(column, value, match_type="exact"):
        """
        Applies filtering logic for string fields based on match_type.
        'exact': column == value
        'ilike_partial': column.ilike(f"%{value}%")
        'ilike_starts_with': column.ilike(f"{value}%")
        Handles list of values, __null__, and __notnull__.
        """
        if isinstance(value, list):
            return column.in_(value)
        elif value == "__null__":
            return column.is_(None)
        elif value == "__notnull__":
            return column.is_not(None)
        else:
            if match_type == "ilike_partial":
                return column.ilike(f"%{value}%")
            elif match_type == "ilike_starts_with":
                return column.ilike(f"{value}%")
            else:  # default to exact
                return column == value

    @property
    def queries(self):
        db_queries = []
        for date_field in DateTimeQuerySchema.allowed_date_fields.keys():
            db_queries.extend(self.dateQueries[date_field].queries)

        for num_field in NumberQuerySchema.allowed_number_fields.keys():
            db_queries.extend(self.numQueries[num_field].queries)

        for str_field in StringQuerySchema.allowed_string_fields.keys():
            db_queries.extend(self.strQueries[str_field].queries)

        if "isCollection" in self.parsed_queries_internal:
            db_queries.append(
                EntityModel.isCollection
                == bool(self.parsed_queries_internal["isCollection"])
            )
        if "isDeleted" in self.parsed_queries_internal:
            db_queries.append(
                EntityModel.isDeleted == bool(self.parsed_queries_internal["isDeleted"])
            )

        """ for field_name, config in self.string_search_field_map.items():
            if field_name in self.parsed_queries_internal:
                db_queries.append(
                    self._apply_string_filter(
                        config["column"],
                        self.parsed_queries_internal[field_name],
                        match_type=config["match_type"],
                    )
                ) """

        return db_queries

    def rawQuery(self, db) -> str:
        try:
            query1 = db.session.query(EntityModel).filter(*self.queries)

            # get the where clause as rawQuery
            statement = query1.statement
            if statement.whereclause is not None:
                # Compile *only* the whereclause part
                return str(
                    statement.whereclause.compile(
                        dialect=sqlite.dialect(),
                        compile_kwargs={"literal_binds": True},
                    )
                )
            else:
                return ""  # No WHERE clause

        except Exception as err:
            return f"Failed to generate, error {err}"

    def get_latest_version(self, db):
        VersionModel = version_class(self.MediaVersion)

        version_query = db.session.query(
            func.min(VersionModel.transaction_id).label("min_version"),
            func.max(VersionModel.transaction_id).label("max_version"),
        ).one()

        min_version = version_query.min_version or 0
        max_version = version_query.max_version or 0
        return max_version, min_version

    def readFromDB(self, query):
        query1 = query.filter(*self.queries)
        result = query1.all()
        return [ItemSchema().dump(item) for item in result]
