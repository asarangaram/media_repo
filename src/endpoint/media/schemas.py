from datetime import datetime
from flask import request
from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import (
    Schema,
    post_dump,
    fields,
    post_load,
)
from werkzeug.exceptions import InternalServerError
from src.endpoint.collection.model import CollectionModel


from clmediakit import (
    IntigerizedBool,
    MediaTypeField,
    MediaType,
    MillisecondsSinceEpoch,
)


class MediaSchemaGET(Schema):
    SKIP_VALUES = set([None, ""])

    class Meta:
        ordered = True  # Enable ordered serialization

    server_uid = fields.Int(attribute="id", data_key="serverUID", dump_only=True)
    collectionLabel = fields.Method("get_collection_label", dump_only=True)

    label = fields.Str(allow_none=True, required=True)
    description = fields.Str(allow_none=True, required=True)
    ref = fields.Str(allow_none=True, required=True)

    addedDate = MillisecondsSinceEpoch(
        required=True, error_messages={"invalid": "addedDate: Invalid date format."}
    )
    updatedDate = MillisecondsSinceEpoch(
        required=True, error_messages={"invalid": "updatedDate: Invalid date format."}
    )
    CreateDate = fields.DateTime(allow_none=True, required=True)
    FileSize = fields.Str(allow_none=True, required=True)
    ImageHeight = fields.Int(allow_none=True, required=True)
    ImageWidth = fields.Int(allow_none=True, required=True)
    Duration = fields.Str(allow_none=True, required=True)
    MIMEType = fields.Str(allow_none=True, required=True)
    md5 = fields.Str(allow_none=True, required=True)

    def get_collection_label(self, obj):
        if hasattr(obj, "collectionId"):
            collection = CollectionModel.find_by_id(obj.collectionId)
            return collection.label
        else:
            raise InternalServerError("couldnot get collection label")

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }


class MediaFileSchemaPOST(Schema):
    media = Upload(required=True, error_messages={"required": "media is required."})


class MediaFileSchemaPUT(Schema):
    media = Upload(required=False)


class MediaSchemaGETQuery(Schema):
    type = fields.List(MediaTypeField(), required=True)
    page = fields.Int(required=False)
    per_page = fields.Int(required=False)

    @post_load
    def convert(self, data, **kwargs):
        # Convert strings to MediaType enum instances
        data["type"] = [MediaType(t) for t in data["type"]]
        return data


class MediaSchemaPOST(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization

    label = fields.Str()
    description = fields.Str()
    collectionLabel = fields.Str(required=True)
    ref = fields.Str(allow_none=True)


class MediaSchemaPUT(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization

    label = fields.Str()
    description = fields.Str()
    collectionLabel = fields.Str()
    ref = fields.Str()
    isDeleted = IntigerizedBool()


class ErrorSchema(Schema):
    err = fields.Str(required=True, error_messages={"required": "err is required."})
    description = fields.Str(
        required=True, error_messages={"required": "collectionId is required."}
    )
