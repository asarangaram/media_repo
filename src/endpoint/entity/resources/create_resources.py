from flask.views import MethodView
from flask import request
from src.endpoint.entity.temp_file import TempFile
from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.custom_handle_error import custom_handle_error
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import (
    CannotAttachFileWithCollectionError,
    MediaMustHaveMediaFile,
    Failed2GetEntityTypeError,
)


def entity_create_resource(MediaVersion, route):
    @route.route("/create")
    class EntityCreate(MethodView):
        @custom_handle_error
        @route.response(201, ItemSchema)
        def post(cls):
            # Validate
            form_data = ItemSchema().load(request.form)
            files = MediaFileSchema().load(request.files)

            if "is_collection" not in form_data and "media" not in files:
                raise Failed2GetEntityTypeError()

            if form_data.get("is_collection", None):
                if files.get("media"):
                    raise CannotAttachFileWithCollectionError()
            else:
                if not files.get("media"):
                    raise MediaMustHaveMediaFile()

            # Analyse media file
            if files.get("media"):
                temp_file = TempFile(files["media"])
                metadata = temp_file.metadata()
            else:
                temp_file = None
                metadata = {}

            # update
            item = EntityModel.create(**form_data, **metadata)

            # clean up
            if temp_file:
                temp_file.remove()

            return item
