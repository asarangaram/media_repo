from datetime import datetime
from flask import request
from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import Schema, ValidationError, fields, post_load, validates_schema, validate


from .media_types import IntigerizedBool, MediaTypeField, MediaType, MillisecondsSinceEpoch


        

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
    createdDate = MillisecondsSinceEpoch( 
        error_messages={"invalid": "createdDate: Invalid date format."}
    )
    
    ref = fields.Str()
    isDeleted = IntigerizedBool()
    notes = fields.List(fields.Int())

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        print(data)
        print(kwargs)
        values =    [data.get(variable)
            for variable in [
                "name",
                "collectionLabel",
                "originalDate",
                "ref",
                "isDeleted",
                "notes",
                'createdDate',
                'updatedDate',
            ]] 
        print (values)


class MediaSchemaPUT(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization
    updatedDate = MillisecondsSinceEpoch(
        error_messages={"invalid": "updatedDate: Invalid date format."}
    )

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
        ## This is not the appropriate place to update
        ## as the file may be sent in PUT call without any form data.
        """ flags =    [data.get(variable) is not None
            for variable in [
                "name",
                "collectionLabel",
                "originalDate",
                "ref",
                "isDeleted",
                "notes",
            ]] 
        
        if not any( flags ):
            raise ValidationError(
                {
                    "empty": ["Nothing to update!"],
                }
            ) """
        print(data)
        print(kwargs)
        values =    [data.get(variable)
            for variable in [
                "name",
                "collectionLabel",
                "originalDate",
                "ref",
                "isDeleted",
                "notes",
                'createdDate',
                'updatedDate',
            ]] 
        print (f'PUT/Incoming: {values}')


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
    fExt = fields.Str(
        required=True,
    )


class ErrorSchema(Schema):
    err = fields.Str(required=True, error_messages={"required": "err is required."})
    description = fields.Str(
        required=True, error_messages={"required": "collectionId is required."}
    )
