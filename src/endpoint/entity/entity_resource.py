from collections import OrderedDict
from marshmallow import ValidationError

from src.endpoint.entity.models import EntityModel, TempFile
from src.endpoint.entity.resources import mask_errors
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import CannotAttachFileWithCollectionError


from clmediakit import CLMetaData
from flask import jsonify, request
from flask.views import MethodView



def entity_resource(MediaVersion, route):
    @route.route("/<int:entity_id>")
    class Media(MethodView):
        """
        Handles operations on individual media entities.
        """

        @mask_errors
        @route.response(200, ItemSchema())
        def get(cls, entity_id: int):
            """
            Retrieves a specific media entity by its ID.

            Args:
                entity_id: The ID of the media entity.

            Returns:
                The media entity as a JSON response.
            """
            entity = EntityModel.get(id=entity_id)
            if not entity:
                return jsonify({"error": "Media not found", "status_code": 404}), 404
            return entity

        @mask_errors
        @route.response(201, ItemSchema)
        def put(cls, entity_id):

            form_data = ItemSchema().load(request.form)
            files = MediaFileSchema().load(request.files)
            # Collection can't have media file
            if form_data.get("isCollection", False):
                if files.get("media"):
                    raise CannotAttachFileWithCollectionError()

            temp_file = None
            metadata = {}
            # process file if given
            if files.get("media"):
                temp_file = TempFile(files["media"])
                metadata = CLMetaData.from_media(temp_file.path).to_dict()

            item = EntityModel.update(entity_id, **form_data, **metadata)

            if temp_file:
                temp_file.remove()
            return item

        def delete(cls, entity_id):
            return EntityModel.delete(entity_id)

    pass
