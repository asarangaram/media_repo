from src.endpoint.entity.models import EntityModel, TempFile
from src.endpoint.entity.resources import mask_errors
from src.endpoint.entity.schema import ItemSchema, MediaFileSchema
from src.utils.custom_errors.validation_errors import CannotAttachFileWithCollectionError


from clmediakit import CLMetaData
from flask import request


def entity_update_resource(MediaVersion, route):
        @route.route("/update/<int:entity_id>")
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