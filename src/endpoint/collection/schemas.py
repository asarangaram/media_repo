from flask_smorest.fields import Upload
from marshmallow import Schema, fields, validates_schema, ValidationError

from ..media.models import MediaModel
from ..media.schemas import MediaSchemaGET


class CollectionSchema(Schema):
    id = fields.Int(required=True)
    label = fields.Str(required=True)
    description = fields.Str()
    createdDate = fields.DateTime(dump_only=True)
    updatedDate = fields.DateTime(dump_only=True)
    media = fields.List(fields.Nested(MediaSchemaGET),  dump_only=True)


class CollectionCreateSchema(Schema):
    label = fields.Str(required=True, error_messages={"required": "label is required."})


class CollectionUpdateSchema(Schema):
    label = fields.Str()
    description = fields.Str()

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        if not data.get("label") and not data.get("description"):
            raise ValidationError("Either 'label' or 'description' must be provided.")


class ErrorSchema(Schema):
    status = fields.Int(required=True, description="HTTP status code")
    message = fields.Str(required=True, description="Error message")
