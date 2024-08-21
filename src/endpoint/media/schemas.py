from datetime import datetime
from flask import request
from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import Schema, ValidationError, fields, post_load, validates_schema, validate


from .media_types import MediaTypeField, MediaType

class MillisecondsSinceEpoch(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return int(value.timestamp() * 1000)
    
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return datetime.fromtimestamp(value / 1000.0)
        except (TypeError, ValueError):
            raise self.make_error("invalid", input=value)


class IntigerizedBool(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return 1 if value else 0
    
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return False if value is 0 else True
        except (TypeError, ValueError):
            raise self.make_error("invalid", input=value)
        

class MediaFileSchemaPOST(Schema):
    media = Upload(required=True, error_messages={"required": "media is required."})


class MediaFileSchemaPUT(Schema):
    media = Upload(required=False)


## All fields are mandatory when reading
## Few are optional for POST, and almost all except id are optional for PUT

class MediaSchemaGETQuery(Schema):
    type = fields.List(MediaTypeField(), required=True)
    
    @post_load
    def convert(self, data, **kwargs):
        # Convert strings to MediaType enum instances
        data['type'] = [MediaType(t) for t in data['type']]
        return data
    

class MediaSchemaPOST(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization

    name = fields.Str()

    collectionLabel = fields.Str(
        required=True, error_messages={"required": "collectionLabel is required."}
    )

    
    originalDate = MillisecondsSinceEpoch(
        error_messages={"invalid": "originalDate: Invalid date format."}
    )
    
    ref = fields.Str()
    isDeleted = IntigerizedBool()
    notes = fields.List(fields.Int())


class MediaSchemaPUT(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization

    name = fields.Str()
    collectionLabel = fields.Str()
    
    originalDate = MillisecondsSinceEpoch(
        error_messages={"invalid": "originalDate: Invalid date format."}
    )
    ref = fields.Str()
    isDeleted = IntigerizedBool()
    notes = fields.List(fields.Int())

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        if not data:
            raise ValidationError(
                {
                    "empty": ["Nothing to update!"],
                }
            )
        flags =    [data.get(variable) is not None
            for variable in [
                "name",
                "collectionLabel",
                "createdDate",
                "originalDate",
                "updatedDate",
                "ref",
                "isDeleted",
                "notes",
            ]] 
        
        if not any( flags ):
            raise ValidationError(
                {
                    "empty": ["Nothing to update!"],
                }
            )


class MediaSchemaGET(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization

    
    server_uid = fields.Int(attribute="id", data_key="serverUID", dump_only=True)
    name = fields.Str(required=True, error_messages={"required": "name is required."})
    type = MediaTypeField(
        enum=MediaType, dump_only=True, error_messages={"required": "type is required."}
    )
    collectionLabel = fields.Str(
        required=True, error_messages={"required": "collectionLabel is required."}
    )
    md5String = fields.Str(
        required=True, error_messages={"required": "md5String is required."}
    )
    createdDate = MillisecondsSinceEpoch(
        required=True, error_messages={"invalid": "createdDate: Invalid date format."}
    )
    originalDate = MillisecondsSinceEpoch(
        error_messages={"invalid": "originalDate: Invalid date format."}
    )
    updatedDate = MillisecondsSinceEpoch(
        required=True, error_messages={"invalid": "updatedDate: Invalid date format."}
    )
    ref = fields.Str(
        required=True,
    )
    isDeleted = IntigerizedBool(
        required=True, error_messages={"required": "isDeleterd is required."}
    )
    notes = fields.List(fields.Int())
    content_type = fields.Str(
        required=True,
    )


class ErrorSchema(Schema):
    err = fields.Str(required=True, error_messages={"required": "err is required."})
    description = fields.Str(
        required=True, error_messages={"required": "collectionId is required."}
    )
