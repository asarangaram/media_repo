from flask import request
from flask.views import MethodView

from src.endpoint.upload.model import UploadManager
from src.endpoint.upload.schema import UploadFileSchema, UploadResponseSchema
from src.utils.custom_errors.custom_handle_error import custom_handle_error
from src.utils.custom_errors.validation_errors import MediaMustHaveMediaFile


def register_sessions_resources(route):
    @route.route("/<string:session_id>/upload")
    class SessionUpload(MethodView):
        @custom_handle_error
        @route.response(201, UploadResponseSchema)
        def post(self, session_id):
            print(request.files)
            files = UploadFileSchema().load(request.files)

            uploaded_file = files.get("media")
            if not uploaded_file:
                raise MediaMustHaveMediaFile()

            manager = UploadManager(session_id, uploaded_file)
            result = manager.upload_files()

            return result

        @custom_handle_error
        @route.response(200)
        def get(self, session_id):
            return {"message": "Post the file to upload"}
