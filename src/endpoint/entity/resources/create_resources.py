from flask.views import MethodView
from flask import request
from src.endpoint.entity.temp_file import TempFile
from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources import mask_errors
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import (
    CannotAttachFileWithCollectionError,
    MediaMustHaveMediaFile,
)


def entity_create_resource(MediaVersion, route):
    @route.route("/create")
    class EntityCreate(MethodView):
        @mask_errors
        @route.response(201, ItemSchema)
        def post(cls):
            # Validate
            form_data = ItemSchema().load(request.form)
            files = MediaFileSchema().load(request.files)

            if form_data.get("isCollection", True) and files.get("media"):
                raise CannotAttachFileWithCollectionError()
            elif not files.get("media"):
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
