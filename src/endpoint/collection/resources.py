from flask import json, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import ValidationError
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound
import logging
from ...db import db

logging.basicConfig(level=logging.DEBUG)

from .schemas import (
    CollectionSchema,
    CollectionCreateSchema,
    CollectionUpdateSchema,
    ErrorSchema,
)
from .model import CollectionModel


collection_bp = Blueprint("collection_bp", __name__, url_prefix="/collection")


@collection_bp.route("/<string:id>")
class Collection(MethodView):
    @collection_bp.response(200, CollectionSchema)
    def get(self, id):
        return CollectionModel.get(id)

    @collection_bp.arguments(CollectionUpdateSchema)
    @collection_bp.response(201, CollectionSchema)
    @collection_bp.alt_response(
        404, ErrorSchema, description="Failed to delete the items"
    )
    def put(self, store_data, id):
        return CollectionModel.update(_id=id, **store_data)

    @collection_bp.response(200)
    @collection_bp.alt_response(
        404, ErrorSchema, description="Failed to delete the items"
    )
    def delete(self, id):
        try:
            store = CollectionModel.delete(id)
            return {"message": f"item {id} deleted"}
        except NotFound as e:
            print(f"NotFound is {e}")
            raise e
        except Exception as e:
            print(f"error is {e}")
            raise NotFound(e)


@collection_bp.route("")
@collection_bp.route("/")
class CollectionList(MethodView):
    @collection_bp.response(200, CollectionSchema(many=True))
    def get(self):
        print("GET /collection")
        return CollectionModel.get_all()

    @collection_bp.alt_response(422, ErrorSchema, description="Validation error")
    @collection_bp.arguments(CollectionCreateSchema)
    @collection_bp.response(201, CollectionSchema)
    def post(self, store_data):
        print("POST /collection")
        return CollectionModel.create(**store_data)


@collection_bp.errorhandler(404)
def not_found_error(error):
    response = {"message": str(error)}
    return jsonify(response), 404

""" 
@collection_bp.errorhandler(422)
def not_found_error(error):
    response = {"message": f"{str(error)}\n Did you forget to add data"}
    return jsonify(response), 404
 """
 
""" @collection_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    # Customize the error response here
    response = {
        "status": 422,
        "message": "Validation error",
        "errors": error.messages
    }
    return jsonify(response), 422

@collection_bp.before_app_request
def before_request():
    # Code to run before each request within the blueprint
    pass """

""" @collection_bp.after_app_request
def after_request(response):
    print(response.content_type)
    # Modify response after request processing
    if response.status_code == 422 and response.content_type == 'application/json':
        # Example of adding custom fields or modifying the response
        data = response.get_json()
        if not data:
            data = {}
        data['custom_field'] = 'This is a custom field'
        response.set_data(json.dumps(data))
    return response """