from flask import request
from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import Schema, ValidationError, fields, validates_schema

from .hash.md5 import validate_md5String

from .media_types import MediaTypeField, MediaType


class MediaFileSchemaPOST(Schema):
    media = Upload(required=True, error_messages={"required": "media is required."})

class MediaFileSchemaPUT(Schema):
    media = Upload(required=False)

## All fields are mandatory when reading
## Few are optional for POST, and almost all except id are optional for PUT

class MediaSchemaPOST(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization
    name = fields.Str()
    type = MediaTypeField(enum=MediaType, required=True, error_messages={"required": "type is required."})
    collectionLabel = fields.Str(required=True,  error_messages={"required": "collectionLabel is required."})
    md5String = fields.Str(required=True,  error_messages={"required": "md5String is required."})
    createdDate = fields.DateTime( error_messages={"invalid": "createdDate: Invalid date format."})
    originalDate = fields.DateTime( error_messages={"invalid": "originalDate: Invalid date format."})
    updatedDate = fields.DateTime( error_messages={"invalid": "updatedDate: Invalid date format."})
    ref = fields.Str()
    isdeleted = fields.Bool()
    notes = fields.List(fields.Int())
    
   

class MediaSchemaPUT(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization
    name = fields.Str()
    type = MediaTypeField()
    collectionLabel = fields.Str()
    md5String = fields.Str()
    createdDate = fields.DateTime( error_messages={"invalid": "createdDate: Invalid date format."})
    originalDate = fields.DateTime( error_messages={"invalid": "originalDate: Invalid date format."})
    updatedDate = fields.DateTime( error_messages={"invalid": "updatedDate: Invalid date format."})
    ref = fields.Str()
    isdeleted = fields.Bool()
    notes = fields.List(fields.Int())
  

class MediaSchemaGET(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, error_messages={"required": "md5String is required."})
    type = MediaTypeField(enum=MediaType, required=True, error_messages={"required": "type is required."})
    collectionLabel = fields.Str(required=True,  error_messages={"required": "collectionLabel is required."})
    md5String = fields.Str(required=True,  error_messages={"required": "md5String is required."})
    createdDate = fields.DateTime(required=True, error_messages={"invalid": "createdDate: Invalid date format."})
    originalDate = fields.DateTime( error_messages={"invalid": "originalDate: Invalid date format."})
    updatedDate = fields.DateTime(required=True, error_messages={"invalid": "updatedDate: Invalid date format."})
    ref = fields.Str(required=True, )
    isdeleted = fields.Bool(required=True, error_messages={"required": "md5String is required."} )
    notes = fields.List(fields.Int())

class ErrorSchema(Schema):
    err = fields.Str(required=True, error_messages={"required": "err is required."})
    description = fields.Str(required=True,error_messages={"required": "collectionId is required."})
