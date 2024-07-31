from flask import request, send_file
from flask import render_template, make_response
from flask.views import MethodView
from flask_smorest import Blueprint

from .schemas import MultipartFileSchema, MediaSchema, ErrorSchema

from .models import MediaModel

media_bp = Blueprint("media_bp", __name__, url_prefix="/media")


@media_bp.route("/upload/form")
class TestUpload(MethodView):
    def get(self):
        headers = {"Content-Type": "text/html"}
        return make_response(render_template("upload_media.html"), 200, headers)


@media_bp.route("/upload")
class Upload(MethodView):
    @media_bp.arguments(MultipartFileSchema, location="files")
    @media_bp.response(201, MediaSchema)
    @media_bp.alt_response(415, ErrorSchema, description="Failed to upload")
    def post(cls, files):
        return MediaModel.create(files["media"])


@media_bp.route("/<int:media_id>/download")
class MediaDownload(MethodView):
    def get(cls, media_id: int):
        media = MediaModel.get(media_id)
        return send_file(media.absolute_path(), mimetype="image/jpeg", download_name=media.name)


@media_bp.route("/<int:media_id>")
class Media(MethodView):
    @media_bp.response(200, MediaSchema)
    def get(cls, media_id: int):
        return MediaModel.get(media_id)

    @media_bp.response(200)
    def delete(cls, media_id: int):
        return MediaModel.delete(media_id)


@media_bp.route("/list")
class MediaList(MethodView):
    @media_bp.response(200, MediaSchema(many=True))
    def get(cls):
        return list(MediaModel.get_all())

    def delete(cls):
        return MediaModel.delete_all()
