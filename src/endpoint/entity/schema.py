from clmediakit import (
    IntigerizedBool,
    MediaTypeField,
    MillisecondsSinceEpoch,
)
from flask_smorest.fields import Upload
from marshmallow import (
    Schema,
    fields,
    post_dump,
    validates_schema,
)

from src.utils.custom_errors.validation_errors import (
    MissingParametersInMatchQuery,
    TooManyParametersInMatchQuery,
)


# Schema for handling media file uploads
class MediaFileSchema(Schema):
    media = Upload(required=False)  # Optional media file upload field


# Schema for representing an item with various metadata fields
class ItemSchema(Schema):
    class Meta:
        ordered = True  # Enable ordered serialization of fields

    # Fields with their respective types and validation rules
    id = fields.Int(dump_only=True)  # Read-only field
    is_collection = IntigerizedBool(
        required=False
    )  # Boolean field indicating if the item is a collection
    label = fields.Str(
        allow_none=True,
        required=False,
        error_messages={"missing label": "TODO"},
    )  # Optional label for the item
    description = fields.Str()  # Description of the item

    parent_id = fields.Int(
        allow_none=True, error_messages={"parent_id": "TODO"}
    )  # Parent item ID
    added_date = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "added_date: Invalid date format."},
    )  # Timestamp when the item was added
    updated_date = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "updated_date: Invalid date format."},
    )  # Timestamp when the item was last updated
    is_deleted = IntigerizedBool(
        # default=False
    )  # Boolean indicating if the item is deleted

    # Additional metadata fields
    create_date = MillisecondsSinceEpoch(
        dump_only=True,
        attribute="create_date",
        data_key="create_date",
    )
    file_size = fields.Int(
        dump_only=True,
        attribute="file_size",
        data_key="file_size",
    )
    image_height = fields.Int(
        dump_only=True,
        attribute="image_height",
        data_key="height",
    )
    image_width = fields.Int(
        dump_only=True,
        attribute="image_width",
        data_key="width",
    )
    duration = fields.Float(
        dump_only=True,
        attribute="duration",
        data_key="duration",
    )
    mime_type = fields.Str(
        dump_only=True,
        attribute="mime_type",
        data_key="mime_type",
    )
    type = MediaTypeField(dump_only=True)
    extension = fields.Str(dump_only=True)

    # d_hash = fields.Str(dump_only=True)  # Commented out field for hash
    md5 = fields.Str(dump_only=True)

    @validates_schema
    def validate_media_info(self, data, **kwargs):
        """
        Validate that media-related fields exist only when is_collection is
        False. If the item is a collection, these fields should not be
        present.
        """

        """ is_collection = bool(data.get("is_collection", False))

        if is_collection:
            if not "label" in data:
                raise ValidationError(f"label is required for collection")
        else:
            if not "create_date" in data:
                raise ValidationError(f"create_date is required for media")
            if not "file_size" in data:
                raise ValidationError(f"file_size is required for media")
            if not "md5" in data:
                raise ValidationError(f"md5 is required for media") """
        pass

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        """
        Remove fields with values in SKIP_VALUES from the serialized output.
        """

        return {key: value for key, value in data.items() if value}


class MatchQuerySchema(Schema):
    id = fields.Int(required=False, allow_none=True)
    md5 = fields.Str(required=False, allow_none=True)
    label = fields.Str(required=False, allow_none=True)

    # Custom validation to ensure only one of id, md5, or label is provided
    @validates_schema
    def validate_one_param(self, data, **kwargs):
        present_params = [
            field for field in ["md5", "label"] if data.get(field) is not None
        ]

        if not present_params:
            raise MissingParametersInMatchQuery()
        elif len(present_params) > 1:
            raise TooManyParametersInMatchQuery()
