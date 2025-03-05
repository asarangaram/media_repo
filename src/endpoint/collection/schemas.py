from flask_smorest.fields import Upload
from marshmallow import Schema, fields, post_dump, validates_schema, ValidationError


from ..media.media_types import IntigerizedBool, MillisecondsSinceEpoch


class CollectionSchema(Schema):
    SKIP_VALUES = set([None, ""])
    server_uid = fields.Int(attribute="id", data_key="serverUID", dump_only=True)

    label = fields.Str(required=True)
    description = fields.Str()
    createdDate = MillisecondsSinceEpoch(dump_only=True)
    updatedDate = MillisecondsSinceEpoch(dump_only=True)
    isDeleted = IntigerizedBool(
        required=True, error_messages={"required": "isDeleted is required."}
    )
    # media = fields.List(fields.Nested(MediaSchemaGET),  dump_only=True)

    media_count = fields.Method("get_media_count", dump_only=True)

    def get_media_count(self, obj):
        if hasattr(obj, "media"):
            return len(obj.media)
        else:
            return 0

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }


class CollectionCreateSchema(Schema):
    label = fields.Str(required=True, error_messages={"required": "label is required."})
    description = fields.Str()
    createdDate = MillisecondsSinceEpoch()
    updatedDate = MillisecondsSinceEpoch()
    isDeleted = IntigerizedBool()

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        label = data.get("label")

        if not label.strip():
            raise ValidationError("label can't be blank")


class CollectionUpdateSchema(Schema):
    # server_uid = fields.Int(attribute="id", data_key="serverUID")
    label = fields.Str()
    description = fields.Str()
    createdDate = MillisecondsSinceEpoch()
    updatedDate = MillisecondsSinceEpoch()
    isDeleted = IntigerizedBool()

    @validates_schema
    def validate_at_least_one(self, data, **kwargs):
        pass
        # print(data)
        """ if not data.get("label") and not data.get("description"):
            raise ValidationError("Either 'label' or 'description' must be provided.") """


class ErrorSchema(Schema):
    status = fields.Int(required=True, metadata={"description": "HTTP status code"})
    message = fields.Str(required=True, metadata={"description": "Error message"})
