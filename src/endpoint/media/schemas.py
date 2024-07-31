from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields

from .media_types import MediaTypeField, MediaType


class MultipartFileSchema(Schema):
    media = Upload()


class MediaSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    type = MediaTypeField(enum=MediaType, required=True)
    datetime = fields.DateTime(required=True)
    sha512hash = fields.Str(required=True)


class ErrorSchema(Schema):
    err = fields.Str(required=True)
    description = fields.Str(required=True)
