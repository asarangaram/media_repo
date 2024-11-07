from marshmallow import Schema, fields

from src.endpoint.landing.models import ServerStatusModel


class LandingPageResultSchema(Schema):
    name = fields.Str(required=True)
    info = fields.Str(required=True)
    id = fields.Int(required=True)
    status = fields.Method("get_status", dump_only=True)

    def get_status(self, obj):
        items = [item.to_json() for item in ServerStatusModel.find_all()]
        
        status = {}
        for d in items:
            status.update(d)
        print(f"status {status}")
        return status
