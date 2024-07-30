from marshmallow import Schema, fields

class LandingPageResultSchema(Schema):
    name = fields.Str(required=True)
    info = fields.Str(required=True)