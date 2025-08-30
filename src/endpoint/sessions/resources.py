import os
import shutil
from flask import abort, request
from flask.views import MethodView
from werkzeug.utils import secure_filename
from src.config import ConfigClass


def register_analysis_resources(MediaVersion, route):
    @route.route("/<string:session_id>/upload")
    class SessionUpload(MethodView):
        @route.response(201)
        def post(self,session_id):
            uploaded_files = request.files.getlist('files')
            if not session_id:
                abort(400, message="file can't be uploaded without session id")

            if not uploaded_files:
                abort(400, message="No file was uploaded.")

            session_folder_path = os.path.join(
                ConfigClass.SESSION_STORAGE_LOCATION, session_id
            )
            if not os.path.exists(session_folder_path):
                os.makedirs(session_folder_path)

            uploaded_file_details = []
            for uploaded_file in uploaded_files:
                original_filename = secure_filename(uploaded_file.filename)
                file_path = os.path.join(session_folder_path, original_filename)

                # Check if the file already exists
                if os.path.exists(file_path):
                    uploaded_file_details.append(
                        {
                            "filename": original_filename,
                            "status": "not uploaded",
                            "error": "File already exists. Not overwritten.",
                        }
                    )
                else:
                    # Save the file
                    uploaded_file.save(file_path)
                    uploaded_file_details.append(
                        {
                            "filename": original_filename,
                            "status": "uploaded successfully",
                        }
                    )
            total_files = len(
                [
                    name
                    for name in os.listdir(session_folder_path)
                    if os.path.isfile(os.path.join(session_folder_path, name))
                ]
            )
            return {
                "message": "Files uploaded successfully",
                "session_id": session_id,
                "session_count": total_files,
                "uploaded_files": uploaded_file_details,
            } 
    @route.route("/<string:session_id>/delete")
    class SessionDelete(MethodView):
        @route.response(201)
        def delete(self,session_id):
            session_folder_path = os.path.join(
                ConfigClass.SESSION_STORAGE_LOCATION, session_id
            )
            if  os.path.exists(session_folder_path):
                shutil.rmtree(session_folder_path)
            return {
                "message": "session wiped",
                "session_id": session_id,
            }
            