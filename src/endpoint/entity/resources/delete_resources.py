from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources import mask_errors


from flask.views import MethodView


def entity_softrestore_resource(MediaVersion, route):
    @route.route("/restore/<int:entity_id>")
    class EntityRestore(MethodView):
        @mask_errors
        def put(cls, entity_id):
            return EntityModel.softrestore(entity_id)


def entity_softdelete_resource(MediaVersion, route):
    @route.route("/to_bin/<int:entity_id>")
    class EntityToBin(MethodView):
        @mask_errors
        def put(cls, entity_id):
            return EntityModel.softdelete(entity_id)


def entity_harddelete_resource(MediaVersion, route):
    @route.route("/delete/<int:entity_id>")
    class EntityDelete(MethodView):
        @mask_errors
        def delete(cls, entity_id):
            return EntityModel.delete(entity_id)
        

def reset(MediaVersion, route):
    @route.route("/delete_all")
    class Reset(MethodView):
        @mask_errors
        def delete(cls):
            raise Exception("reset is disabled; ")
            return EntityModel.delete_all()      

    