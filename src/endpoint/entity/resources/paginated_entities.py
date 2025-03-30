from collections import OrderedDict
from flask import jsonify, request
from flask.views import MethodView
from sqlalchemy_continuum import version_class
from sqlalchemy import func

from src.db import db
from src.endpoint.entity.schema import ItemSchema, ItemsQuerySchema
from .blueprint import entity_bp


def create_resource_paginated_entities(MediaVersion):
    @entity_bp.route("/page")
    class PaginatedEntitiesResource(MethodView):
        @entity_bp.arguments(ItemsQuerySchema, location="query")
        @entity_bp.response(200)
        def get(cls, kwargs):
            current_version = request.args.get("current_version", type=int)
            last_known_version = request.args.get("last_known_version", type=int)
            page = request.args.get("page", default=1, type=int)
            per_page = request.args.get("per_page", None, type=int)

            if page > 1 and (current_version is None or per_page is None):
                return (
                    jsonify(
                        {
                            "error": "current_version and per_page are required to get further pages"
                        }
                    ),
                    400,
                )

            try:
                VersionModel = version_class(MediaVersion)

                version_query = db.session.query(
                    func.min(VersionModel.transaction_id).label("min_version"),
                    func.max(VersionModel.transaction_id).label("max_version"),
                ).one()

                min_version = 0  # Force minimum version to 0
                max_version = version_query.max_version or 0

                effective_current_version = (
                    current_version if current_version is not None else max_version
                )
                effective_last_version = (
                    last_known_version
                    if last_known_version is not None
                    else min_version
                )

                if effective_current_version < effective_last_version:
                    return (
                        jsonify(
                            {
                                "error": "Current version must be greater than or equal to last known version"
                            }
                        ),
                        400,
                    )

                if max_version > 0 and (
                    effective_current_version > max_version
                    or effective_last_version < min_version
                ):
                    return jsonify({"error": "Version numbers out of range"}), 400

                subquery = (
                    MediaVersion.query.filter(
                        VersionModel.transaction_id > effective_last_version,
                        VersionModel.transaction_id <= effective_current_version,
                    )
                    .group_by(MediaVersion.id)
                    .subquery()
                )

                query = db.session.query(MediaVersion).join(
                    subquery,
                    (MediaVersion.id == subquery.c.id)
                    & (MediaVersion.transaction_id == subquery.c.transaction_id),
                )

                # Apply filters from kwargs
                filters = {
                    getattr(MediaVersion, key): value
                    for key, value in kwargs.items()
                    if key in MediaVersion.__table__.columns
                }

                if (
                    MediaVersion.parentId in filters
                    and filters[MediaVersion.parentId] == 0
                ):
                    filters[MediaVersion.parentId] = None

                query = query.filter(*[col == val for col, val in filters.items()])

                total_items = query.count()

                if per_page:
                    total_pages = (total_items + per_page - 1) // per_page
                    paginated_query = (
                        query.order_by(VersionModel.id.desc())
                        .limit(per_page)
                        .offset((page - 1) * per_page)
                    )
                    paginated = paginated_query.all()
                else:
                    paginated = query.all()
                    total_pages = 1

                items = [ItemSchema().dump(item) for item in paginated]

                response = OrderedDict()
                response["items"] = items
                response["metaInfo"] = {
                    "currentVersion": effective_current_version,
                    "lastSyncedVersion": effective_last_version,
                    "latestVersion": max_version,
                }
                if per_page:
                    response["metaInfo"]["pagination"] = {
                        "currentPage": page,
                        "perPage": per_page if per_page else total_items,
                        "totalItems": total_items,
                        "totalPages": total_pages,
                    }

                return jsonify(response), 200

            except Exception as e:
                MediaVersion.rollback()
                print(str(e))
                return jsonify({"error": str(e)}), 500
