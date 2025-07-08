from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.custom_handle_error import custom_handle_error


from flask.views import MethodView


def entity_softrestore_resource(MediaVersion, route):
    @route.route("/<int:entity_id>/restore")
    class EntityRestore(MethodView):
        @custom_handle_error
        def put(cls, entity_id):
            return EntityModel.softrestore(entity_id)


def entity_softdelete_resource(MediaVersion, route):
    @route.route("/<int:entity_id>/to_bin")
    class EntityToBin(MethodView):
        @custom_handle_error
        def put(cls, entity_id):
            return EntityModel.softdelete(entity_id)


def entity_harddelete_resource(MediaVersion, route):
    @route.route("/<int:entity_id>/delete")
    class EntityDelete(MethodView):
        @custom_handle_error
        def delete(cls, entity_id):
            return EntityModel.delete(entity_id)
        

def reset(MediaVersion, route):
    @route.route("/reset")
    class Reset(MethodView):
        @custom_handle_error
        def delete(cls):
            raise Exception("reset is disabled; ")
            return EntityModel.delete_all()      

    