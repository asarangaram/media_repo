from flask import request, send_file
from flask import render_template, make_response

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from werkzeug.exceptions import UnsupportedMediaType

import logging

from .schemas import MultipartFileSchema, ImageSchema,ErrorSchema

from .models import ImageModel

image_bp = Blueprint("image_bp", __name__, url_prefix="/image")

class RepoException(Exception):
    pass


@image_bp.route("/upload")
class Upload(MethodView):
    @image_bp.arguments(MultipartFileSchema, location="files")
    @image_bp.response(201, ImageSchema)
    @image_bp.alt_response(415, ErrorSchema, description="Filed to upload")
    def post(cls, files):
        logging.debug("post called")
        image = files["image"]
        if image.filename == "":
            logging.debug("No image name provided")
            raise UnsupportedMediaType('Image name is not specified')
        object, err = ImageModel.create(image=image)
        if err :
            raise UnsupportedMediaType(str(err))
        if not object :
            raise UnsupportedMediaType('unexpected error')
            
        return object
    

@image_bp.route('/upload/form')
class TestUpload(MethodView):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('upload.html'), 200,
                             headers)

@image_bp.route("/<int:image_id>")
class Image(MethodView):
    def get(cls, image_id: int):
        try:
            image, e = ImageModel.get(image_id)
            if e:
                return {"message": e}, 400

            return send_file(
                image.path, mimetype="image/jpeg", download_name=image.name
            )

        except Exception as e:
            return {"message": e}, 400

    def delete(cls, image_id: int):
        e = ImageModel.delete(image_id)
        if e:
            return {"message": e}, 400
        return {"success": "Image deleted successfully"}

@image_bp.route("/list")
class Images(MethodView):
    def get(cls):
        all, e = ImageModel.get_all()
        if e:
            return {"message": e}, 400
        return {"images": all}, 201

    def delete(cls):
        all, e = ImageModel.delete_all()
        if e:
            return {"message": e}, 400
        return {"images": all}, 201

@image_bp.route("/<int:image_id>/metadata")
class ImageMetadata(MethodView):
    def get(cls, image_id: int):
        metadata, e = ImageModel.get_metadata_by_id(image_id)
        if e:
            return {"message": e}, 400

        return metadata, 201

@image_bp.route("/<int:image_id>/thumbnail")
class ImageThumbnail(MethodView):
    def get(cls, image_id: int):
        try:
            image, e = ImageModel.get(image_id)
            if e:
                return {"message": e}, 400
            thumbnail, e = image.get_thumbnail_path()
            if e:
                return {"message": e}, 400
            return send_file(
                thumbnail, mimetype="image/jpeg", download_name=f"{image_id}_thumbnail.png"
            )

        except Exception as e:
            return {"message": e}, 400
