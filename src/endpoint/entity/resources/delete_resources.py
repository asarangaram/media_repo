from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.custom_handle_error import custom_handle_error


from flask.views import MethodView


def entity_softrestore_resource(MediaVersion, route):
    @route.route("/restore/<int:entity_id>")
    class EntityRestore(MethodView):
        @custom_handle_error
        def put(cls, entity_id):
            return EntityModel.softrestore(entity_id)


def entity_softdelete_resource(MediaVersion, route):
    @route.route("/to_bin/<int:entity_id>")
    class EntityToBin(MethodView):
        @custom_handle_error
        def put(cls, entity_id):
            return EntityModel.softdelete(entity_id)


def entity_harddelete_resource(MediaVersion, route):
    @route.route("/delete/<int:entity_id>")
    class EntityDelete(MethodView):
        @custom_handle_error
        def delete(cls, entity_id):
            return EntityModel.delete(entity_id)
        

def reset(MediaVersion, route):
    @route.route("/delete_all")
    class Reset(MethodView):
        @custom_handle_error
        def delete(cls):
            raise Exception("reset is disabled; ")
            return EntityModel.delete_all()      

    