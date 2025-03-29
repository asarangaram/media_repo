from collections import OrderedDict
from datetime import datetime
from functools import wraps
from io import BytesIO
import os
from flask import jsonify, request, send_file, send_from_directory
from flask import render_template, make_response
from flask.views import MethodView
from flask_smorest import Blueprint

from werkzeug.utils import secure_filename
from werkzeug.exceptions import InternalServerError, NotFound
from clmediakit import MediaType, CLMetaData

from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.errors import (
    MissingMediaFileError,
    NoFileForCollectionError,
    PreviewGenerationFailedError,
    VideoStreamError,
)


from ...db import db
from sqlalchemy import func
from sqlalchemy_continuum import version_class


entity_bp = Blueprint("entity_bp", __name__, url_prefix="/entity")

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


def create_entity_resources(MediaVersion):
    @entity_bp.route("/")
    @entity_bp.route("")
    class MediaList(MethodView):
        @entity_bp.arguments(MediaFileSchema, location="files")
        @entity_bp.arguments(ItemSchema, location="form")
        @entity_bp.response(201, ItemSchema)
        def post(cls, files, kwargs):
            if not kwargs.get("isCollection", False):
                if not files.get("media"):
                    raise MissingMediaFileError()
                metadata = CLMetaData.from_media(
                    EntityModel.save(files["media"])
                ).to_dict()
            else:
                if files.get("media"):
                    raise NoFileForCollectionError()
                metadata = {}

            item = EntityModel.create(**kwargs, **metadata)
            if metadata.get("filePath"):
                os.remove(metadata.get("filePath"))
            return item

        @entity_bp.response(200)
        def delete(cls):
            return EntityModel.delete_all()

    @entity_bp.route("/<int:entity_id>")
    class Media(MethodView):
        def get(cls, entity_id: int):
            pass

        @entity_bp.response(200)
        def delete(cls, entity_id: int):
            pass

        def put(cls, files, kwargs, entity_id):
            pass

    @entity_bp.route("/upload")
    class MediaUploadForm(MethodView):
        def get(self):
            headers = {"Content-Type": "text/html"}
            return make_response(render_template("upload_media.html"), 200, headers)

    @entity_bp.route("/<int:entity_id>/download")
    class MediaDownload(MethodView):
        def get(cls, entity_id: int):
            entity: EntityModel | None = EntityModel.get(entity_id)
            if not entity:
                raise MissingMediaFileError()
            if entity.isCollection:
                raise NoFileForCollectionError()
            return send_file(
                entity.absolute_filename(),
                mimetype=entity.content_type,
                download_name=secure_filename(f"{entity.md5}.{entity.extension}"),
            )

    @entity_bp.route("/<int:entity_id>/preview")
    class PreviewDownload(MethodView):
        def get(cls, entity_id: int):
            entity = EntityModel.get(entity_id)
            if not entity:
                raise MissingMediaFileError()
            if entity.isCollection:
                raise NoFileForCollectionError()  # consider creating preview
            if os.path.exists(entity.absolute_preview_filename()):
                return send_file(
                    entity.absolute_preview_filename(),
                    mimetype="image/jpeg",
                    download_name=secure_filename(f"{entity.md5}_preview.jpeg"),
                )

    @entity_bp.route("/<int:entity_id>/stream/m3u8")
    class get_m3u8(MethodView):
        def get(cls, entity_id: int):
            entity = EntityModel.get(entity_id)
            if not entity:
                raise MissingMediaFileError()
            if entity.isCollection:
                raise NoFileForCollectionError()
            stream_folder = entity.get_stream_folder()
            return send_from_directory(
                stream_folder, "adaptive.m3u8", as_attachment=False
            )

    @entity_bp.route("/<int:entity_id>/stream/<string:filename>")
    class get_segment(MethodView):
        def get(cls, entity_id: int, filename: str):
            entity = EntityModel.get(entity_id)
            if not entity:
                raise MissingMediaFileError()
            if entity.isCollection:
                raise NoFileForCollectionError()
            stream_folder = entity.get_stream_folder()
            if filename.endswith(".ts"):
                return send_from_directory(stream_folder, filename, as_attachment=False)
            if filename.endswith(".m3u8"):
                return send_from_directory(stream_folder, filename, as_attachment=False)
            else:
                raise VideoStreamError(
                    id=entity_id, additionalMessage="Invalid file type"
                )


@entity_bp.errorhandler(404)
def not_found_error(error):
    response = {"message": str(error)}
    return jsonify(response), 404
