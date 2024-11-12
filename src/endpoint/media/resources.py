from datetime import datetime
from functools import wraps
from io import BytesIO
import os
import subprocess
from flask import Response, jsonify, request, send_file, send_from_directory
from flask import render_template, make_response
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_rangerequest import RangeRequest

from werkzeug.utils import secure_filename
from werkzeug.exceptions import  InternalServerError, NotFound
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
        return list(MediaModel.get_all(types=kargs['type'] ))

    @media_bp.response(200)
    def delete(cls):
        return MediaModel.delete_all()


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
        return send_file(
            media.absolute_path(), mimetype=media.content_type, download_name=media.name
        )

@media_bp.route("/<int:media_id>/preview")
class PreviewDownload(MethodView):
    def get(cls, media_id: int):
        media = MediaModel.get(media_id)
        return send_file(
            media.preview_path(), mimetype=media.content_type, download_name=media.name
        )

STREAM_FOLDER = "/disks/data/git/github/asarangaram/dash_experiment/VID_20240206_095544"
M3U8_FILE = "adaptive.m3u8"
MP4_FILE = "VID_20240206_095544.mp4"

@media_bp.route("/<int:media_id>/stream/mp4")
class get_mp4(MethodView):
    def get(cls, media_id: int):
        try:
            file = os.path.join(STREAM_FOLDER, "random_seekable.mp4")
            if not os.path.exists(file):
                command = [
                    'ffmpeg', '-y',
                    '-i', os.path.join(STREAM_FOLDER, MP4_FILE), 
                    '-movflags', '+faststart', 
                    '-vf', 'scale=-1:720',
                    '-c:a', 'copy',
                    file
                ]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                print(process.stderr.read())
            if not os.path.exists(file):
                raise NotFound( description="failed to get file for rendering")
                
            
            size = os.path.getsize(file)
            with open(file, 'rb') as f:
                etag = RangeRequest.make_etag(f)
            last_modified = datetime.now()
            response = RangeRequest(open(file, 'rb'),
                        etag=etag,
                        last_modified=last_modified,
                        size=size).make_response()
            response.content_type = "video/mp4"
            return response
        except FileNotFoundError:
            raise NotFound( description="MP4 file not found")
        except Exception as e:
            raise InternalServerError(f"{e}\nprocess.stderr.read()\ncommand")

@media_bp.route("/<int:media_id>/stream/m3u8")
class get_m3u8(MethodView):
    def get(cls, media_id: int):
        try:
            return send_from_directory(STREAM_FOLDER, M3U8_FILE, as_attachment=False)
        except FileNotFoundError:
            raise NotFound( description="M3U8 file not found")

@media_bp.route("/<int:media_id>/stream/<string:filename>")
class get_segment(MethodView):
    def get(cls, media_id: int, filename: str):
        if filename.endswith(".ts"):
            try:
                return send_from_directory(STREAM_FOLDER, filename, as_attachment=False)
            except FileNotFoundError:
                raise NotFound( description="Segment file not found")
        if filename.endswith(".m3u8"):
            try:
                return send_from_directory(STREAM_FOLDER, filename, as_attachment=False)
            except FileNotFoundError:
                raise NotFound( description="Segment file not found")
        else:
            raise NotFound( description="Invalid file type requested")
    
@media_bp.errorhandler(404)
def not_found_error(error):
    response = {"message": str(error)}
    return jsonify(response), 404
