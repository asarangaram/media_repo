from typing import Optional
from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.custom_handle_error import custom_handle_error


from flask import jsonify, send_file, send_from_directory
from flask.views import MethodView
from werkzeug.utils import secure_filename


import os


def blob_download_media(MediaVersion, route):
    @route.route("/<int:entity_id>/download/media")
    class EntityMediaFile(MethodView):
        """
        Handles downloading of media files.
        """

        @custom_handle_error
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
                return (
                    jsonify({"error": "Media not found", "status_code": 404}),
                    404,
                )
            if entity.is_collection:
                return (
                    jsonify(
                        {"error": "No file for collection", "status_code": 400}
                    ),
                    400,
                )
            if not os.path.exists(entity.absolute_filename):
                return (
                    jsonify(
                        {"error": "Media file missing", "status_code": 404}
                    ),
                    404,
                )
            return send_file(
                entity.absolute_filename,
                mimetype=entity.mime_type,
                download_name=secure_filename(entity.filename),
            )


def blob_download_preview(MediaVersion, route):
    @route.route("/<int:entity_id>/download/preview")
    class EntityPreviewFile(MethodView):
        """
        Handles downloading of preview images for media files.
        """

        @custom_handle_error
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
                return (
                    jsonify({"error": "Media not found", "status_code": 404}),
                    404,
                )
            if entity.is_collection:
                return (
                    jsonify(
                        {"error": "No file for collection", "status_code": 400}
                    ),
                    400,
                )
            if os.path.exists(entity.absolute_preview_filename):
                return send_file(
                    entity.absolute_preview_filename,
                    mimetype="image/jpeg",
                    download_name=secure_filename(entity.preview_filename),
                )
            return (
                jsonify(
                    {"error": "Preview file missing", "status_code": 404}
                ),
                404,
            )


def blob_download_video_stream(MediaVersion, route):
    @route.route("/<int:entity_id>/stream/m3u8")
    class EntityGetM3U8(MethodView):
        """
        Serves the adaptive streaming manifest file (m3u8) for a media
        entity.
        """

        @custom_handle_error
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
                return (
                    jsonify({"error": "Media not found", "status_code": 404}),
                    404,
                )
            if entity.is_collection:
                return (
                    jsonify(
                        {"error": "No file for collection", "status_code": 400}
                    ),
                    400,
                )
            stream_folder = entity.get_stream_folder()
            return send_from_directory(
                stream_folder, "adaptive.m3u8", as_attachment=False
            )

    @route.route("/<int:entity_id>/stream/<string:filename>")
    class EntityGetSegment(MethodView):
        """
        Serves individual streaming segments or manifest files for a media
        entity.
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
                return (
                    jsonify({"error": "Media not found", "status_code": 404}),
                    404,
                )
            if entity.is_collection:
                return (
                    jsonify(
                        {"error": "No file for collection", "status_code": 400}
                    ),
                    400,
                )
            stream_folder = entity.get_stream_folder()
            if filename.endswith((".ts", ".m3u8")):
                return send_from_directory(
                    stream_folder, filename, as_attachment=False
                )
            return (
                jsonify(
                    {
                        "error": f"File '{filename}' is not available in the "
                        "stream folder",
                        "status_code": 404,
                    }
                ),
                404,
            )
