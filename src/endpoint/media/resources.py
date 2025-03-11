from collections import OrderedDict
from datetime import datetime
from functools import wraps
from io import BytesIO
from flask import jsonify, request, send_file, send_from_directory
from flask import render_template, make_response
from flask.views import MethodView
from flask_smorest import Blueprint

from werkzeug.utils import secure_filename
from werkzeug.exceptions import InternalServerError, NotFound
from .media_types import MediaType

from .schemas import (
    MediaFileSchemaPOST,
    MediaFileSchemaPUT,
    MediaSchemaPOST,
    MediaSchemaPUT,
    MediaSchemaGET,
    MediaSchemaGETQuery,
    ErrorSchema,
)
from ...db import db
from sqlalchemy import func
from sqlalchemy_continuum import version_class
from .models import MediaModel

media_bp = Blueprint("media_bp", __name__, url_prefix="/media")

enableLogging = False


def mask_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if enableLogging:
            form_data = request.form.to_dict()
            print(f"Incoming Request Data: {form_data}")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise InternalServerError(f"{e}")

    return wrapper


def create_media_resources(MediaVersion):
    @media_bp.route("/")
    @media_bp.route("")
    class MediaList(MethodView):
        @mask_errors
        @media_bp.arguments(MediaFileSchemaPOST, location="files")
        @media_bp.arguments(MediaSchemaPOST, location="form")
        @media_bp.response(201, MediaSchemaGET)
        @media_bp.alt_response(415, ErrorSchema, description="Failed to create")
        def post(cls, files, kwargs):
            bytes_io = BytesIO()
            files["media"].save(bytes_io)
            argsExtra = {}
            argsExtra["bytes_io"] = bytes_io
            if not kwargs.get("name"):
                argsExtra["name"] = files["media"].filename
            argsExtra["filename"] = secure_filename(files["media"].filename)
            argsExtra["content_type"] = files["media"].content_type

            return MediaModel.create(**kwargs, **argsExtra)

        @media_bp.response(200, MediaSchemaGET(many=True))
        @media_bp.arguments(MediaSchemaGETQuery, location="query")
        def get(cls, kargs):
            # print((kargs['type'][0]))
            # print(type(kargs['type'][0]))
            res = list(MediaModel.get_all(types=kargs["type"]))
            return res

        @media_bp.response(200)
        def delete(cls):
            return MediaModel.delete_all()

    @media_bp.route("/page")
    class PaginatedResource(MethodView):
        @media_bp.arguments(MediaSchemaGETQuery, location="query")
        @media_bp.response(200)
        def get(cls, kargs):
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

                # Get min and max versions available
                version_query = db.session.query(
                    func.min(VersionModel.transaction_id).label("min_version"),
                    func.max(VersionModel.transaction_id).label("max_version"),
                ).one()

                min_version = (
                    version_query.min_version or 0
                )  # Handle case with no versions
                # min version, bettter to set 0
                # need to investigate why the min version is set to 2
                # in version query.
                min_version = 0
                max_version = version_query.max_version or 0

                # Set defaults if versions are not provided
                effective_current_version = (
                    current_version if current_version is not None else max_version
                )
                effective_last_version = (
                    last_known_version
                    if last_known_version is not None
                    else min_version
                )

                # Validate versions
                if effective_current_version < effective_last_version:
                    return (
                        jsonify(
                            {
                                "error": "Current version must be greater than or equal to last known version"
                            }
                        ),
                        400,
                    )

                if max_version > 0:  # Only check bounds if we have versions
                    if (
                        effective_current_version > max_version
                        or effective_last_version < min_version
                    ):
                        return jsonify({"error": "Version numbers out of range"}), 400

                # Base query for modified items
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

                # Get total count for pagination
                total_items = query.count()

                # Apply pagination
                if per_page:
                    total_pages = (total_items + per_page - 1) // per_page
                    paginated_query = (
                        query.order_by(VersionModel.id.desc())
                        .limit(per_page)
                        .offset((page - 1) * per_page)
                    )

                    # Execute query
                    paginated = paginated_query.all()
                else:
                    paginated = query.all()
                    total_pages = 1

                items = [MediaSchemaGET().dump(item) for item in paginated]

                # Format response
                response = OrderedDict()

                response["items"] = items

                response["metaInfo"] = {
                    "currentVersion": effective_current_version,
                    "lastSyncedVersion": effective_last_version,
                    "latestVersion": max_version,
                    # "updates_available": effective_current_version < max_version,
                }
                if per_page:
                    response["metaInfo"]["pagination"] = {
                        "currentPage": page,
                        "perPage": per_page if per_page else total_items,
                        "totalItems": total_items,
                        "totalPages": total_pages,
                        # "hasNext": page < total_pages,
                        # "hasPrevious": page > 1,
                    }

                return jsonify(response), 200

            except Exception as e:
                MediaVersion.rollback()
                print(str(e))
                return jsonify({"error": str(e)}), 500

    @media_bp.route("/<int:media_id>")
    class Media(MethodView):
        @media_bp.response(200, MediaSchemaGET)
        def get(cls, media_id: int):
            return MediaModel.get(media_id)

        @media_bp.response(200)
        def delete(cls, media_id: int):
            media = MediaModel.get(media_id)
            if media:
                MediaModel.delete(media_id)
                return True
            return False

        @mask_errors
        @media_bp.arguments(MediaFileSchemaPUT, location="files")
        @media_bp.arguments(MediaSchemaPUT, location="form")
        @media_bp.response(200, MediaSchemaGET)
        @media_bp.alt_response(415, ErrorSchema, description="Failed to update")
        def put(cls, files, kwargs, media_id):
            bytes_io = None
            argsExtra = {}
            if files.get("media"):
                bytes_io = BytesIO()
                files["media"].save(bytes_io)

                argsExtra["bytes_io"] = bytes_io
                argsExtra["filename"] = secure_filename(files["media"].filename)
                argsExtra["content_type"] = files["media"].content_type
            mediaType = kwargs.get("type")
            if mediaType:
                kwargs["type"] = MediaType[kwargs.get("type").upper()]
            return MediaModel.update(media_id, **kwargs, **argsExtra)

    @media_bp.route("/upload")
    class MediaUploadForm(MethodView):
        def get(self):
            headers = {"Content-Type": "text/html"}
            return make_response(render_template("upload_media.html"), 200, headers)

    @media_bp.route("/<int:media_id>/download")
    class MediaDownload(MethodView):
        def get(cls, media_id: int):
            media = MediaModel.get(media_id)
            if not media:
                NotFound("Media not found")
            return send_file(
                media.absolute_path(),
                mimetype=media.content_type,
                download_name=media.name,
            )

    @media_bp.route("/<int:media_id>/preview")
    class PreviewDownload(MethodView):
        def get(cls, media_id: int):
            media = MediaModel.get(media_id)
            if not media:
                NotFound("Media not found")
            return send_file(
                media.preview_path(),
                mimetype=media.content_type,
                download_name=media.name,
            )

    @media_bp.route("/<int:media_id>/stream/m3u8")
    class get_m3u8(MethodView):
        def get(cls, media_id: int):
            media = MediaModel.get(media_id)
            if not media:
                NotFound("Media not found")
            stream_folder = media.get_stream_folder()
            try:
                return send_from_directory(
                    stream_folder, "adaptive.m3u8", as_attachment=False
                )
            except FileNotFoundError:
                raise NotFound(description="M3U8 file not found")

    @media_bp.route("/<int:media_id>/stream/<string:filename>")
    class get_segment(MethodView):
        def get(cls, media_id: int, filename: str):
            media = MediaModel.get(media_id)
            if not media:
                NotFound("Media not found")
            stream_folder = media.get_stream_folder()
            if filename.endswith(".ts"):
                try:
                    return send_from_directory(
                        stream_folder, filename, as_attachment=False
                    )
                except FileNotFoundError:
                    raise NotFound(description="Segment file not found")
            if filename.endswith(".m3u8"):
                try:
                    return send_from_directory(
                        stream_folder, filename, as_attachment=False
                    )
                except FileNotFoundError:
                    raise NotFound(description="Segment file not found")
            else:
                raise NotFound(description="Invalid file type requested")


@media_bp.errorhandler(404)
def not_found_error(error):
    response = {"message": str(error)}
    return jsonify(response), 404
