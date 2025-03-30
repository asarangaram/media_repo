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

from src.endpoint.entity.models import EntityModel, TempFile
from src.endpoint.entity.resources.paginated_entities import (
    create_resource_paginated_entities,
)
from src.endpoint.entity.schema import ItemSchema, ItemsQuerySchema, MediaFileSchema
from src.utils.errors import (
    MissingMediaError,
    MissingMediaFileError,
    MissingMediaWhenUploadError,
    NoFileForCollectionError,
    PreviewGenerationFailedError,
    VideoStreamError,
)


from sqlalchemy import func
from sqlalchemy_continuum import version_class
from .blueprint import entity_bp, mask_errors


def create_entity_resources(MediaVersion):
    create_resource_paginated_entities(MediaVersion)

    @entity_bp.route("/")
    @entity_bp.route("")
    class MediaList(MethodView):
        @mask_errors
        @entity_bp.arguments(MediaFileSchema, location="files")
        @entity_bp.arguments(ItemSchema, location="form")
        @entity_bp.response(201, ItemSchema)
        def post(cls, files, kwargs):
            temp_file = None
            if not kwargs.get("isCollection", False):
                if not files.get("media"):
                    raise MissingMediaWhenUploadError()
                temp_file = TempFile(files["media"])
                metadata = CLMetaData.from_media(temp_file.path).to_dict()
            else:
                if files.get("media"):
                    raise NoFileForCollectionError()
                metadata = {}

            item = EntityModel.create(**kwargs, **metadata)
            if temp_file:
                temp_file.remove()
            return item

        @mask_errors
        @entity_bp.arguments(ItemsQuerySchema, location="query")
        @entity_bp.response(200, ItemSchema(many=True))
        def get(cls, query_args):
            return EntityModel.get_all(**query_args)

        @entity_bp.response(200)
        def delete(cls):
            return EntityModel.delete_all()

    @entity_bp.route("/<int:entity_id>")
    class Media(MethodView):
        @mask_errors
        @entity_bp.response(200, ItemSchema())
        def get(cls, entity_id: int):
            entity = EntityModel.get(id=entity_id)
            if not entity:
                raise MissingMediaFileError()
            return entity

        @entity_bp.response(200)
        def delete(cls, entity_id: int):
            pass

        def put(cls, files, kwargs, entity_id):
            pass

    @entity_bp.route("/upload")
    class MediaUploadForm(MethodView):
        @mask_errors
        def get(self):
            headers = {"Content-Type": "text/html"}
            return make_response(render_template("upload_media.html"), 200, headers)

    @entity_bp.route("/<int:entity_id>/download")
    class MediaDownload(MethodView):
        @mask_errors
        def get(cls, entity_id: int):
            entity: EntityModel | None = EntityModel.get(id=entity_id)
            if not entity:
                raise MissingMediaError()
            if entity.isCollection:
                raise NoFileForCollectionError()
            if not os.path.exists(entity.absolute_filename):
                raise MissingMediaFileError()
            return send_file(
                entity.absolute_filename,
                mimetype=entity.MIMEType,
                download_name=secure_filename(entity.filename),
            )

    @entity_bp.route("/<int:entity_id>/preview")
    class PreviewDownload(MethodView):
        @mask_errors
        def get(cls, entity_id: int):
            entity = EntityModel.get(id=entity_id)
            if not entity:
                raise MissingMediaFileError()
            if entity.isCollection:
                raise NoFileForCollectionError()  # consider creating preview
            if os.path.exists(entity.absolute_preview_filename):
                return send_file(
                    entity.absolute_preview_filename,
                    mimetype="image/jpeg",
                    download_name=secure_filename(entity.preview_filename),
                )

    @entity_bp.route("/<int:entity_id>/stream/m3u8")
    class get_m3u8(MethodView):
        @mask_errors
        def get(cls, entity_id: int):
            entity = EntityModel.get(id=entity_id)
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
            entity = EntityModel.get(id=entity_id)
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
    response = {
        "error": error.description,  # Default error message
        "status_code": 404,
    }
    return response, 404
