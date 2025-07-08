from typing import Optional
from src.db import db
from src.endpoint.entity.entity_resource import entity_resource
from src.endpoint.entity.models import EntityModel, TempFile
from src.endpoint.entity.resources import mask_errors
from src.endpoint.entity.schema import ItemSchema, ItemsQuerySchema, MediaFileSchema


from clmediakit import CLMetaData
from flask import (
    jsonify,
    make_response,
    render_template,
    send_file,
    send_from_directory,
)
from flask.views import MethodView
from sqlalchemy import func
from sqlalchemy_continuum import version_class
from werkzeug.utils import secure_filename


import logging
import os
from collections import OrderedDict

def create_entity_resources(MediaVersion, route):
    """
    Registers routes and handlers for media-related operations.

    Args:
        MediaVersion: The SQLAlchemy model representing media versions.
    """

    entity_resource(MediaVersion, route)

    @route.route("/")
    @route.route("")
    class MediaList(MethodView):
        """
        Handles operations on the list of media entities, including creation, retrieval, and deletion.
        """

        @mask_errors
        @route.arguments(MediaFileSchema, location="files")
        @route.arguments(ItemSchema, location="form")
        @route.response(201, ItemSchema)
        def post(cls, files, kwargs):
            """
            Creates a new media entity.

            Args:
                files: The uploaded media files.
                kwargs: Additional metadata for the media entity.

            Returns:
                The created media entity as a JSON response.
            """
            temp_file = None
            if not kwargs.get("isCollection", False):
                if not files.get("media"):
                    return (
                        jsonify(
                            {"error": "Post media with a file.", "status_code": 400}
                        ),
                        400,
                    )

                temp_file = TempFile(files["media"])
                metadata = CLMetaData.from_media(temp_file.path).to_dict()
            else:
                if files.get("media"):
                    return (
                        jsonify(
                            {
                                "error": "Can't attach file to Collection",
                                "status_code": 400,
                            }
                        ),
                        400,
                    )

                metadata = {}

            item = EntityModel.create(**kwargs, **metadata)
            if temp_file:
                temp_file.remove()
            return item

        @mask_errors
        @route.arguments(ItemsQuerySchema, location="query")
        @route.response(200)
        def get(cls, kwargs):
            """
            Retrieves a paginated list of media entities.

            Args:
                kwargs: Query parameters for filtering and pagination.

            Returns:
                A JSON response containing the list of media entities and metadata.
            """
            current_version = kwargs.get("current_version")
            last_known_version = kwargs.get("last_known_version")
            page = kwargs.get("page", 1)
            per_page = kwargs.get("per_page")

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

                query_filters = []
                for col, val in filters.items():
                    if isinstance(val, (list, tuple)):  # Handle multiple values
                        query_filters.append(col.in_(val))
                    else:  # Handle single value
                        query_filters.append(col == val)

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
                return jsonify({"error": str(e), "status_code": 500}), 500

        @route.response(200)
        def delete(cls):
            """
            Deletes all media entities.

            Returns:
                A success response.
            """
            return EntityModel.delete_all()

    

    @route.route("/upload")
    class MediaUploadForm(MethodView):
        """
        Provides an HTML form for uploading media files.
        """

        @mask_errors
        def get(self):
            """
            Renders the media upload form.

            Returns:
                An HTML response containing the upload form.
            """
            headers = {"Content-Type": "text/html"}
            return make_response(render_template("upload_media.html"), 200, headers)

    @route.route("/<int:entity_id>/download")
    class MediaDownload(MethodView):
        """
        Handles downloading of media files.
        """

        @mask_errors
        def get(cls, entity_id: int):
            """
            Downloads a specific media file.

            Args:
                entity_id: The ID of the media entity.

            Returns:
                The media file as a downloadable response.
            """
            entity: Optional[EntityModel] = EntityModel.get(id=entity_id)
            if not entity:
                return jsonify({"error": "Media not found", "status_code": 404}), 404
            if entity.isCollection:
                return (
                    jsonify({"error": "No file for collection", "status_code": 400}),
                    400,
                )
            if not os.path.exists(entity.absolute_filename):
                return jsonify({"error": "Media file missing", "status_code": 404}), 404
            return send_file(
                entity.absolute_filename,
                mimetype=entity.MIMEType,
                download_name=secure_filename(entity.filename),
            )

    @route.route("/<int:entity_id>/preview")
    class PreviewDownload(MethodView):
        """
        Handles downloading of preview images for media files.
        """

        @mask_errors
        def get(cls, entity_id: int):
            """
            Downloads the preview image for a specific media file.

            Args:
                entity_id: The ID of the media entity.

            Returns:
                The preview image as a downloadable response.
            """
            entity = EntityModel.get(id=entity_id)
            if not entity:
                return jsonify({"error": "Media not found", "status_code": 404}), 404
            if entity.isCollection:
                return (
                    jsonify({"error": "No file for collection", "status_code": 400}),
                    400,
                )
            if os.path.exists(entity.absolute_preview_filename):
                return send_file(
                    entity.absolute_preview_filename,
                    mimetype="image/jpeg",
                    download_name=secure_filename(entity.preview_filename),
                )
            return jsonify({"error": "Preview file missing", "status_code": 404}), 404

    @route.route("/<int:entity_id>/stream/m3u8")
    class get_m3u8(MethodView):
        """
        Serves the adaptive streaming manifest file (m3u8) for a media entity.
        """

        @mask_errors
        def get(cls, entity_id: int):
            """
            Retrieves the m3u8 manifest file for adaptive streaming.

            Args:
                entity_id: The ID of the media entity.

            Returns:
                The m3u8 file as a response.
            """
            entity = EntityModel.get(id=entity_id)
            if not entity:
                return jsonify({"error": "Media not found", "status_code": 404}), 404
            if entity.isCollection:
                return (
                    jsonify({"error": "No file for collection", "status_code": 400}),
                    400,
                )
            stream_folder = entity.get_stream_folder()
            return send_from_directory(
                stream_folder, "adaptive.m3u8", as_attachment=False
            )

    @route.route("/<int:entity_id>/stream/<string:filename>")
    class get_segment(MethodView):
        """
        Serves individual streaming segments or manifest files for a media entity.
        """

        def get(cls, entity_id: int, filename: str):
            """
            Retrieves a specific streaming segment or manifest file.

            Args:
                entity_id: The ID of the media entity.
                filename: The name of the file to retrieve.

            Returns:
                The requested file as a response.
            """
            entity = EntityModel.get(id=entity_id)
            if not entity:
                return jsonify({"error": "Media not found", "status_code": 404}), 404
            if entity.isCollection:
                return (
                    jsonify({"error": "No file for collection", "status_code": 400}),
                    400,
                )
            stream_folder = entity.get_stream_folder()
            if filename.endswith((".ts", ".m3u8")):
                return send_from_directory(stream_folder, filename, as_attachment=False)
            return (
                jsonify(
                    {
                        "error": f"File '{filename}' is not available in the stream folder",
                        "status_code": 404,
                    }
                ),
                404,
            )
