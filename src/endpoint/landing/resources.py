from flask.views import MethodView
from flask_smorest import Blueprint, abort

from .models import LandingPageModel
from .schemas import  LandingPageResultSchema

from ...endpoint.collection.schemas import CollectionSchema

landing_bp = Blueprint('landing_bp', __name__, url_prefix='')

@landing_bp.route('/', defaults={'name': None})
@landing_bp.route('/<string:name>')
class LandingPage(MethodView):
    @landing_bp.response(200, LandingPageResultSchema)
    def get(self, name):
        try:
            if name is None:
                page = LandingPageModel()
            else:
                page = LandingPageModel(name)
        except:
            abort(404, message="Landing page not found.")
        return page


def get_field_details(schema_cls):
    fields_map = {}
    for field_name, field in schema_cls().fields.items():
        field_type = type(field).__name__
        required = field.required
        fields_map[field_name] = {'type': field_type, 'required': required}
    return fields_map


@landing_bp.route("/schema")
class CollectionFields(MethodView):
    @landing_bp.response(200)
    def get(self):
        return {"endpoint": "collection", "fields": get_field_details(CollectionSchema)}