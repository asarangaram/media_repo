from marshmallow import Schema, fields

from flask_smorest.fields import Upload
from clmediakit import (
    MediaTypeField,
    MillisecondsSinceEpoch,
)


class UploadFileSchema(Schema):
    media = Upload(required=True)


class UploadResponseSchema(Schema):
    file_identifier = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    MIMEType = fields.Str(
        dump_only=True,
        attribute="MIMEType",
        data_key="mimeType",
    )
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
    type = MediaTypeField(dump_only=True)
    extension = fields.Str(dump_only=True)
    md5 = fields.Str(dump_only=True)
