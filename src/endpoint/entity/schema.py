from flask_smorest.fields import Upload
from marshmallow import post_dump, validates_schema, ValidationError, pre_load, Schema
from clmediakit import (
    IntigerizedBool,
    MediaTypeField,
    MediaType,
    MillisecondsSinceEpoch,
)
from marshmallow import (
    Schema,
    post_dump,
    fields,
    post_load,
)


# Schema for handling media file uploads
class MediaFileSchema(Schema):
    media = Upload(required=False)  # Optional media file upload field


# Schema for representing an item with various metadata fields
class ItemSchema(Schema):
    SKIP_VALUES = set([None, ""])  # Values to skip during serialization

    class Meta:
        ordered = True  # Enable ordered serialization of fields

    # Fields with their respective types and validation rules
    id = fields.Int(dump_only=True)  # Read-only field
    isCollection = IntigerizedBool(
        required=True, error_messages={"missing isCollection": "TODO"}
    )  # Boolean field indicating if the item is a collection
    label = fields.Str(
        allow_none=True, required=False, error_messages={"missing label": "TODO"}
    )  # Optional label for the item
    description = fields.Str()  # Description of the item

    parentId = fields.Int(
        allow_none=True, error_messages={"parentId": "TODO"}
    )  # Parent item ID
    addedDate = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "addedDate: Invalid date format."},
    )  # Timestamp when the item was added
    updatedDate = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "updatedDate: Invalid date format."},
    )  # Timestamp when the item was last updated
    isDeleted = IntigerizedBool(
        default=False
    )  # Boolean indicating if the item is deleted

    # Additional metadata fields
    CreateDate = MillisecondsSinceEpoch(dump_only=True)
    FileSize = fields.Str(dump_only=True)
    ImageHeight = fields.Int(dump_only=True)
    ImageWidth = fields.Int(dump_only=True)
    Duration = fields.Str(dump_only=True)
    MIMEType = fields.Str(dump_only=True)
    # dHash = fields.Str(dump_only=True)  # Commented out field for hash
    md5 = fields.Str(dump_only=True)

    @validates_schema
    def validate_media_info(self, data, **kwargs):
        """
        Validate that media-related fields exist only when isCollection is False.
        If the item is a collection, these fields should not be present.
        """
        media_fields = [
            "FileSize",
            "md5",
            "MIMEType",
        ]
        optional_fields = [
            "CreateDate",
            "Duration",
            "ImageHeight",
            "ImageWidth",
            "dHash",
        ]

        is_collection = bool(data.get("isCollection", False))

        if is_collection and not "label" in data:
            raise ValidationError(f"label is required for collection")

        if is_collection:
            # If it's a collection, these fields should not be present
            for field in media_fields + optional_fields:
                if field in data:
                    raise ValidationError(
                        f"{field} is not allowed for collections", field
                    )

    @pre_load
    def ensure_is_collection(self, data, **kwargs):
        """
        Ensure isCollection is always a boolean (prevents issues when parsing).
        Raise a validation error if isCollection is missing.
        """
        if "isCollection" not in data:
            raise ValidationError("isCollection is required")
        # data["isCollection"] = bool(data["isCollection"])  # Uncomment if needed
        return data

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        """
        Remove fields with values in SKIP_VALUES from the serialized output.
        """
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }


# Schema for querying items with various filters and pagination options
class ItemsQuerySchema(Schema):
    # Queryable fields
    id = fields.Int()
    isCollection = IntigerizedBool()
    label = fields.Str()
    parentId = fields.Int(allow_none=True)
    addedDate = MillisecondsSinceEpoch()
    updatedDate = MillisecondsSinceEpoch()
    isDeleted = IntigerizedBool()
    CreateDate = MillisecondsSinceEpoch()
    FileSize = fields.Str()
    ImageHeight = fields.Int()
    ImageWidth = fields.Int()
    Duration = fields.Str()
    MIMEType = fields.Str()
    # dHash = fields.Str()  # Commented out field for hash
    md5 = fields.Str()

    # Additional query parameters
    current_version = fields.Int()  # Current version of the item
    last_known_version = fields.Int()  # Last known version of the item
    page = fields.Int()  # Pagination: page number
    per_page = fields.Int()  # Pagination: items per page

    similar_to = fields.Int()  # ID of an item to find similar items
    any = IntigerizedBool()  # Boolean flag for additional filtering

    ## TODO:
    ## Add support for range queries for dates, width, height, and duration
    ## Determine whether to use OR or AND for combining filters
