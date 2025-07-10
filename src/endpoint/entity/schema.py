from flask_smorest.fields import Upload
from marshmallow import post_dump, validates_schema, Schema
from clmediakit import (
    IntigerizedBool,
    MediaTypeField,
    MillisecondsSinceEpoch,
)
from marshmallow import (
    fields,
)

from src.utils.custom_errors.validation_errors import (
    MissingParametersInMatchQuery,
    TooManyParametersinMatchQuery,
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
    isCollection = IntigerizedBool(
        required=False
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
        # default=False
    )  # Boolean indicating if the item is deleted

    # Additional metadata fields
    CreateDate = MillisecondsSinceEpoch(
        dump_only=True,
        attribute="CreateDate",
        data_key="createDate",
    )
    FileSize = fields.Int(
        dump_only=True,
        attribute="FileSize",
        data_key="fileSize",
    )
    ImageHeight = fields.Int(
        dump_only=True,
        attribute="ImageHeight",
        data_key="height",
    )
    ImageWidth = fields.Int(
        dump_only=True,
        attribute="ImageWidth",
        data_key="width",
    )
    Duration = fields.Float(
        dump_only=True,
        attribute="Duration",
        data_key="duration",
    )
    MIMEType = fields.Str(
        dump_only=True,
        attribute="MIMEType",
        data_key="mimeType",
    )
    type = MediaTypeField(dump_only=True)
    extension = fields.Str(dump_only=True)

    # dHash = fields.Str(dump_only=True)  # Commented out field for hash
    md5 = fields.Str(dump_only=True)

    @validates_schema
    def validate_media_info(self, data, **kwargs):
        """
        Validate that media-related fields exist only when isCollection is False.
        If the item is a collection, these fields should not be present.
        """

        """ is_collection = bool(data.get("isCollection", False))

        if is_collection:
            if not "label" in data:
                raise ValidationError(f"label is required for collection")
        else:
            if not "CreateDate" in data:
                raise ValidationError(f"CreateDate is required for media")
            if not "FileSize" in data:
                raise ValidationError(f"FileSize is required for media")
            if not "md5" in data:
                raise ValidationError(f"md5 is required for media") """
        pass

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        """
        Remove fields with values in SKIP_VALUES from the serialized output.
        """

        return {key: value for key, value in data.items() if value}


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
    type = fields.List(MediaTypeField())
    extension = fields.List(fields.Str())

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


class MatchQuerySchema(Schema):
    id = fields.Int(required=False, allow_none=True)
    md5 = fields.Str(required=False, allow_none=True)
    label = fields.Str(required=False, allow_none=True)

    # Custom validation to ensure only one of id, md5, or label is provided
    @validates_schema
    def validate_one_param(self, data, **kwargs):
        present_params = [
            field for field in [ "md5", "label"] if data.get(field) is not None
        ]

        if not present_params:
            raise MissingParametersInMatchQuery()
        elif len(present_params) > 1:
            raise TooManyParametersinMatchQuery()
