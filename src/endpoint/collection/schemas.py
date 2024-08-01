from flask_smorest.fields import Upload
from marshmallow import Schema, fields, validates_schema, ValidationError


class CollectionSchema(Schema):
    id = fields.Int(required=True)
    label = fields.Str(required=True)
    description = fields.Str()


class CollectionCreateSchema(Schema):
    label = fields.Str(required=True)


class CollectionUpdateSchema(Schema):
    label = fields.Str()
    description = fields.Str()
    
    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        if not data.get('label') and not data.get('description'):
            raise ValidationError("Either 'label' or 'description' must be provided.")

class ErrorSchema(Schema):
    err = fields.Str(required=True)
    description = fields.Str(required=True)