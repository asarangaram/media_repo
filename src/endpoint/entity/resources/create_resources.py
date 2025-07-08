from flask import make_response, render_template
from src.endpoint.entity.models import EntityModel, TempFile
from src.endpoint.entity.resources import mask_errors
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import CannotAttachFileWithCollectionError, MediaMustHaveMediaFile


from clmediakit import CLMetaData
from flask.views import MethodView


def entity_create_resource(MediaVersion, route):
    @route.route("/create")
    class EntityCreate(MethodView):
        """
        Handles operations on the list of media entities, including creation, retrieval, and deletion.
        """

        @mask_errors
        @route.arguments(MediaFileSchema, location="files")
        @route.arguments(ItemSchema, location="form")
        @route.response(201, ItemSchema)
        def post(cls, files, kwargs):
            """
            Creates a new media entity.

            Args:
                files: The uploaded media files.
                kwargs: Additional metadata for the media entity.

            Returns:
                The created media entity as a JSON response.
            """
            temp_file = None
            if not kwargs.get("isCollection", False):
                if not files.get("media"):
                    raise MediaMustHaveMediaFile()

                temp_file = TempFile(files["media"])
                metadata = CLMetaData.from_media(temp_file.path).to_dict()
            else:
                if files.get("media"):
                    raise CannotAttachFileWithCollectionError()

                metadata = {}

            item = EntityModel.create(**kwargs, **metadata)
            if temp_file:
                temp_file.remove()
            return item
    pass


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