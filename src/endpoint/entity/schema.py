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


class MediaFileSchema(Schema):
    media = Upload(required=False)


class ItemSchema(Schema):
    SKIP_VALUES = set([None, ""])

    class Meta:
        ordered = True  # Enable ordered serialization

    id = fields.Int(dump_only=True)
    label = fields.Str(allow_none=True, required=True)
    description = fields.Str()
    isCollection = IntigerizedBool(required=True)
    parentId = fields.Int(allow_none=True, required=True)
    addedDate = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "addedDate: Invalid date format."},
    )
    updatedDate = MillisecondsSinceEpoch(
        required=True,
        dump_only=True,
        error_messages={"invalid": "updatedDate: Invalid date format."},
    )
    isDeleted = IntigerizedBool(required=True)

    CreateDate = fields.DateTime(dump_only=True)  # May be allow to update?
    FileSize = fields.Str(dump_only=True)
    ImageHeight = fields.Int(dump_only=True)
    ImageWidth = fields.Int(dump_only=True)
    Duration = fields.Str(dump_only=True)
    MIMEType = fields.Str(dump_only=True)
    dHash = fields.Str(dump_only=True)
    md5 = fields.Str(dump_only=True)

    @validates_schema
    def validate_media_info(self, data, **kwargs):
        """Validate that MediaInfo fields exist only when isCollection is False"""
        media_fields = [
            "FileSize",
            "md5",
            "MIMEType",
        ]
        optioal_fields = [
            "CreateDate",
            "Duration",
            "ImageHeight",
            "ImageWidth",
            "dHash",
        ]

        is_collection = data.get("isCollection", False)

        if is_collection:
            # If it's a collection, these fields should not be present
            for field in media_fields + optioal_fields:
                if field in data:
                    raise ValidationError(
                        f"{field} is not allowed for collections", field
                    )
        else:
            # If it's media, ensure required media fields are present
            missing_fields = [field for field in media_fields if field not in data]
            if missing_fields:
                raise ValidationError(
                    f"Missing required media fields: {', '.join(missing_fields)}"
                )

    @pre_load
    def ensure_is_collection(self, data, **kwargs):
        """Ensure isCollection is always a boolean (prevents issues when parsing)"""
        if "isCollection" not in data:
            raise ValidationError("isCollection is required")
        data["isCollection"] = bool(data["isCollection"])
        return data

    """ @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items() if value not in self.SKIP_VALUES
        }
    """
