from marshmallow import Schema, fields


class LandingPageResultSchema(Schema):
    name = fields.Str(required=True)
    info = fields.Str(required=True)
    id = fields.Int(required=True)
    status = fields.Method("get_status", dump_only=True)

    def get_status(self, obj):
        return {"status": "running"}
