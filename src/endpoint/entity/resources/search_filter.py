from flask import request
from sqlalchemy import func
from sqlalchemy.dialects import sqlite
from sqlalchemy_continuum import version_class
from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources.search_schema.search_schema import SearchSchema
from src.endpoint.entity.schema import ItemSchema


class SearchFilters:
    def __init__(self, MediaVersion):
        self.MediaVersion = MediaVersion
        query_args = request.args.to_dict(flat=False)
        self.search_schema = SearchSchema(query_args)

    @property
    def parsed_queries(self):
        return self.search_schema.fields

    def rawQuery(self, db) -> str:
        try:
            query1 = db.session.query(EntityModel).filter(
                *self.search_schema.queries
            )

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
        query1 = query.filter(*self.search_schema.queries)
        result = query1.all()
        return [ItemSchema().dump(item) for item in result]
