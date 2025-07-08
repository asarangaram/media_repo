from flask.views import MethodView
from flask import request
from src.endpoint.entity.temp_file import TempFile
from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.custom_handle_error import custom_handle_error
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import (
    CannotAttachFileWithCollectionError,
)


def entity_update_resource(MediaVersion, route):
    @route.route("/update/<int:entity_id>")
    class EntityUpdate(MethodView):
        @custom_handle_error
        @route.response(201, ItemSchema)
        def put(cls, entity_id):
            # Validate
            form_data = ItemSchema().load(request.form)
            files = MediaFileSchema().load(request.files)

            if form_data.get("isCollection", True) and files.get("media"):
                raise CannotAttachFileWithCollectionError()

            # Analyse media file
            if files.get("media"):
                temp_file = TempFile(files["media"])
                metadata = temp_file.metadata()
            else:
                temp_file = None
                metadata = {}

            # update
            item = EntityModel.update(entity_id, **form_data, **metadata)

            # clean up
            if temp_file:
                temp_file.remove()

            return item
