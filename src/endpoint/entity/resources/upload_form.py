from src.endpoint.entity.resources import mask_errors


from flask import make_response, render_template
from flask.views import MethodView


def entity_upload_form(MediaVersion, route):
    @route.route("/uploadform")
    class MediaUploadForm(MethodView):
        """
        Provides an HTML form for uploading media files.
        """

        @mask_errors
        def get(self):
            """
            Renders the media upload form.

            Returns:
                An HTML response containing the upload form.
            """
            headers = {"Content-Type": "text/html"}
            return make_response(render_template("upload_media.html"), 200, headers)