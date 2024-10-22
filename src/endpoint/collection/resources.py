from flask import json, jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import ValidationError
from werkzeug.exceptions import  NotFound, InternalServerError
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

    @collection_bp.arguments(CollectionUpdateSchema, location="form")
    @collection_bp.response(201, CollectionSchema)
    @collection_bp.alt_response(
        404, ErrorSchema, description="Failed to update the items"
    )
    def put(self, store_data, id):
        return CollectionModel.update(id=id, **store_data)

    @collection_bp.response(200)
    @collection_bp.alt_response(
        404, ErrorSchema, description="Failed to delete the items"
    )
    def delete(self, id):
        try:
            store = CollectionModel.delete(id)
            return {"message": f"item {id} deleted"}
        except NotFound as e:
            #print(f"NotFound is {e}")
            raise e
        except InternalServerError as e:
            raise e 
        except Exception as e:
            #print(f"error is {e}")
            raise NotFound(e)


@collection_bp.route("")
@collection_bp.route("/")
class CollectionList(MethodView):
    @collection_bp.response(200, CollectionSchema(many=True))
    def get(self):
        #print("GET /collection")
        return CollectionModel.get_all()

    @collection_bp.alt_response(422, ErrorSchema, description="Validation error")
    @collection_bp.arguments(CollectionCreateSchema, location="form")
    @collection_bp.response(201, CollectionSchema)
    def post(self, store_data):
        #print("POST /collection")
        return CollectionModel.create(**store_data)



    
