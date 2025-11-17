from marshmallow import (
    Schema,
    fields,
)


class BGTaskSchema(Schema):
    # server_uid = fields.Int(attribute="id", data_key="serverUID")
    media_id = fields.Str()
    task_name = fields.Str()
    task_id = fields.Str()
    task_status = fields.Str()
