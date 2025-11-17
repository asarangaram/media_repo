from src.db import db
from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources.search_filter import SearchFilters
from src.utils.custom_errors.internal_server_errors import UnexpectedFailure
from src.utils.custom_errors.custom_handle_error import custom_handle_error
from src.endpoint.entity.schema import ItemSchema, MatchQuerySchema


from flask import jsonify, request
from flask.views import MethodView

from collections import OrderedDict

from src.utils.custom_errors.not_found_errors import MissingMediaError


def entity_match_resource(MediaVersion, route):
    @route.route("/match")
    class MatchEntity(MethodView):
        """
        search for a Entity, based on its unique attritube.
        The order in which search is being performed is fixed.
        if id is provided,
            search by id and return.
        else if md5 is provided
            search by md5 and return
        else if label is provided
            is_collection=True is automatically added and the label is
            searched for the combination of (is_collection=True, label)
            and return.

        as per the DB Design, its impossible to have more than one items for
        these searches, hence we either return or return not found error.
        """

        @custom_handle_error
        @route.response(200, ItemSchema())
        def get(cls):
            query_data = MatchQuerySchema().load(request.args)

            md5_hash = query_data.get("md5")
            entity_label = query_data.get("label")

            entity = EntityModel.match(
                md5=md5_hash,
                label=entity_label,
            )
            return entity


def entity_read_all_resource(MediaVersion, route):
    @route.route("/filter/loopback")
    class ValidateQuerySchema(MethodView):
        @custom_handle_error
        def get(cls, **kwargs):
            media_query = SearchFilters(MediaVersion, **kwargs)
            return {
                "loopback": media_query.parsed_queries,
                "rawQuery": media_query.rawQuery(db),
            }

    @route.route("/all")
    class EntityList(MethodView):
        """
        Handles operations on the list of media entities, including
        creation, retrieval, and deletion.
        """

        @custom_handle_error
        @route.response(200)
        def get(cls):
            """
            Retrieves a paginated list of media entities.

            Args:
                kwargs: Query parameters for filtering and pagination.

            Returns:
                A JSON response containing the list of media entities and
                metadata.
            """
            media_query = SearchFilters(MediaVersion)
            try:
                items = media_query.readFromDB(
                    db.session.query(EntityModel)
                )
                max_version, _ = media_query.get_latest_version(db)

                response = OrderedDict()

                response["items"] = items
                response["metaInfo"] = {
                    "currentVersion": max_version,
                    "latestVersion": max_version,
                    "totalItems": len(items),
                }
                return jsonify(response), 200

            except Exception:
                db.session.rollback()
                raise UnexpectedFailure()

            """ current_version = kwargs.get("current_version")
            last_known_version = kwargs.get("last_known_version")
            page = kwargs.get("page", 1)
            per_page = kwargs.get("per_page")

            if page > 1 and (current_version is None or per_page is None):
                return (
                    jsonify(
                        {
                            "error": "current_version and per_page are "
                            "required to get further pages"
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

                min_version = version_query.min_version or 0
                max_version = version_query.max_version or 0

                effective_current_version = (
                    current_version if current_version is not None
                    else max_version
                )
                effective_last_version = (
                    last_known_version
                    if last_known_version is not None
                    else min_version
                )

                if effective_current_version < effective_last_version:
                    return jsonify(
                        {
                            "error": "Current version must be greater than or "
                            "equal to last known version"
                        }
                    ), 400

                if max_version > 0 and (
                    effective_current_version > max_version
                    or effective_last_version < min_version
                ):
                    return jsonify(
                        {"error": "Version numbers out of range"}
                    ), 400

                latest_subquery = (
                    db.session.query(
                        MediaVersion.id.label("id"),
                        func.max(VersionModel.transaction_id).label(
                            "max_transaction_id"
                        ),
                    )
                    .filter(
                        VersionModel.transaction_id > effective_last_version,
                        VersionModel.transaction_id <=
                        effective_current_version,
                    )
                    .group_by(MediaVersion.id)
                    .subquery()
                )

                query = db.session.query(MediaVersion).join(
                    latest_subquery,
                    (MediaVersion.id == latest_subquery.c.id)
                    & (
                        MediaVersion.transaction_id
                        == latest_subquery.c.max_transaction_id
                    ),
                )

                query_filters = dbFilter(kwargs)
                query = query.filter(*query_filters)

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
                    orderred_query = query.order_by(VersionModel.id.desc())
                    paginated = orderred_query.all()
                    total_pages = 1

                items = [ItemSchema().dump(item) for item in paginated]

                response = OrderedDict()
                response["items"] = items
                response["metaInfo"] = {
                    "currentVersion": effective_current_version,
                    "lastSyncedVersion": effective_last_version,
                    "latestVersion": max_version,
                    "totalItems": total_items,
                }
                if per_page:
                    response["metaInfo"]["pagination"] = {
                        "currentPage": page,
                        "perPage": per_page if per_page else total_items,
                        "totalPages": total_pages,
                    }

                return jsonify(response), 200

            except Exception as e:
                logging.error(f"Error in MediaList.get: {str(e)}")
                db.session.rollback()
                return jsonify({"error": str(e), "status_code": 500}), 500 """


def entity_read_resource(MediaVersion, route):
    @route.route("/<int:entity_id>")
    class Entity(MethodView):
        """
        Handles operations on individual media entities.
        """

        @custom_handle_error
        @route.response(200, ItemSchema())
        def get(cls, entity_id: int):
            """
            Retrieves a specific media entity by its ID.

            Args:
                entity_id: The ID of the media entity.

            Returns:
                The media entity as a JSON response.
            """
            entity = EntityModel.get(id=entity_id)
            if not entity:
                raise MissingMediaError()
            return entity
