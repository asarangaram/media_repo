from flask_smorest.fields import Upload
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields

class MultipartFileSchema(Schema):
    image = Upload()




class ImageSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    datetime = fields.DateTime(required=True)
    sha512hash = fields.Str(required=True)

class ErrorSchema(Schema):
    err = fields.Str(required=True)
    description= fields.Str(required=True)