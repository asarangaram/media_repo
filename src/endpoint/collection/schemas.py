from flask_smorest.fields import Upload
from marshmallow import Schema, fields, post_dump, validates_schema, ValidationError



from ..media.media_types import  MillisecondsSinceEpoch

class CollectionSchema(Schema):
    SKIP_VALUES = set([None, ''])
    server_uid = fields.Int(attribute="id", data_key="serverUID", dump_only=True)
    
    label = fields.Str(required=True)
    description = fields.Str()
    createdDate = MillisecondsSinceEpoch(dump_only=True)
    updatedDate = MillisecondsSinceEpoch(dump_only=True)
    # media = fields.List(fields.Nested(MediaSchemaGET),  dump_only=True)

    media_count = fields.Method("get_media_count", dump_only=True)

    def get_media_count(self, obj):
        return len(obj.media)
    
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items()
            if value not in self.SKIP_VALUES
        }


class CollectionCreateSchema(Schema):
    label = fields.Str(required=True, error_messages={"required": "label is required."})


class CollectionUpdateSchema(Schema):
    label = fields.Str()
    description = fields.Str()
    server_uid = fields.Int(attribute="id", data_key="serverUID")
    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        if not data.get("label") and not data.get("description"):
            raise ValidationError("Either 'label' or 'description' must be provided.")


class ErrorSchema(Schema):
    status = fields.Int(required=True, metadata={"description":"HTTP status code"})
    message = fields.Str(required=True, metadata={"description":"Error message"})

