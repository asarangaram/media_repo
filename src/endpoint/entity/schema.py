from flask_smorest.fields import Upload
from marshmallow import INCLUDE, ValidationError, post_dump, validates_schema, Schema
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
    NonZeroUIntSearchFieldError,
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


def validate_nonzero_uint_search_term(value):
    if value in ("__null__", "__notnull__"):
        return

    if isinstance(value, int):
        if value > 0:
            return
        raise ValidationError(
            f"must be a positive non-zero integer. (received: {value})"
        )
    if isinstance(value, list):
        if all(isinstance(v, int) and v > 0 for v in value):
            return
        raise ValidationError(
            f"must contain only positive non-zero integers. (received {value})"
        )
    raise ValidationError(
        'must be a positive non-zero integer, a list of such integers, or "__null__" / "__notnull__".'
    )


def validate_str_search_term(value):
    if value in ("__null__", "__notnull__"):
        return
    if isinstance(value, str):
        return
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return
        raise ValidationError(f"must contain only strings. (received {value})")
    raise ValidationError(
        'must be a positive non-zero integer, a list of such integers, or "__null__" / "__notnull__".'
    )


class NonZeroUIntSearchField(fields.Field):
    """
    Accepts:
    - single string like '10'
    - list of strings like ['10', '20']
    - special strings '__null__' or '__notnull__'

    Converts to:
    - int, list of ints, or special strings
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list):
            if len(value) == 1:
                if value[0] in ("__null__", "__notnull__"):
                    return value[0]
                return self._parse_one(value[0], value, attr)

            return [self._parse_one(v, value, attr) for v in value]
        if value in ("__null__", "__notnull__"):
            return value
        return self._parse_one(value, value, attr)

    def _parse_one(self, v, value, attr):
        try:
            num = int(v)
        except (ValueError, TypeError):
            raise NonZeroUIntSearchFieldError(attr, value)
        if num <= 0:
            raise NonZeroUIntSearchFieldError(attr, value)
        return num


class StringSearchField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list):
            if len(value) == 1:
                if value[0] in ("__null__", "__notnull__"):
                    return value[0]
                return value[0]

            return value
        elif isinstance(value, str):
            return value
        else:
            raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code


class BoolSearchField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, list):
            if len(value) == 1:
                if value[0] in ("__null__", "__notnull__"):
                    return value[0]
                return self._parse_one(value[0], value, attr)

            return [self._parse_one(v, value, attr) for v in value]
        if value in ("__null__", "__notnull__"):
            return value
        return self._parse_one(value, value, attr)

    def _parse_one(self, v, value, attr):
        try:
            num = int(v)
        except (ValueError, TypeError):
            raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
        if num != 0 and num != 1:
            raise NonZeroUIntSearchFieldError(attr, value)  #   FIX Error code
        return num == 1


# Schema for querying items with various filters and pagination options
class ItemsQuerySchema(Schema):
    class Meta:
        unknown = INCLUDE  # so unknown fields stay in data

    # Queryable fields
    # Boolean flags
    isCollection = fields.Bool(allow_none=True)
    isDeleted = fields.Bool(allow_none=True)

    # Strings or List of Strings
    label = StringSearchField(allow_none=True)
    label_starts_with = fields.Str(allow_none=True)
    label_contains = fields.Str(allow_none=True)
    description_contains = fields.Str(allow_none=True)

    MIMEType = StringSearchField(allow_none=True)
    type = StringSearchField(allow_none=True)
    extension = StringSearchField(allow_none=True)

    
    

    # nonzero uint or list of nonzero uint
   
    parentId = NonZeroUIntSearchField(allow_none=True)
    id = NonZeroUIntSearchField(allow_none=True)
    

    

    # Additional query parameters
    current_version = fields.Int()  # Current version of the item
    last_known_version = fields.Int()  # Last known version of the item
    page = fields.Int()  # Pagination: page number
    per_page = fields.Int()  # Pagination: items per page

    similar_to = fields.Int()  # ID of an item to find similar items
    any = IntigerizedBool()  # Boolean flag for additional filtering


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
            raise TooManyParametersinMatchQuery()
