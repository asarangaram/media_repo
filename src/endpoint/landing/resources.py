from flask.views import MethodView
from flask_smorest import Blueprint, abort

from src.utils.custom_errors.custom_handle_error import custom_handle_error

from .models import LandingPageModel
from .schemas import LandingPageResultSchema

""" from ...endpoint.collection.schemas import CollectionSchema """

landing_bp = Blueprint("landing_bp", __name__, url_prefix="")


@landing_bp.route("/")
class LandingPage(MethodView):
    @custom_handle_error
    @landing_bp.response(200, LandingPageResultSchema)
    def get(self, name):
        page = LandingPageModel()
        return page


def get_field_details(schema_cls):
    fields_map = {}
    for field_name, field in schema_cls().fields.items():
        field_type = type(field).__name__
        required = field.required
        fields_map[field_name] = {"type": field_type, "required": required}
    return fields_map


""" @landing_bp.route("/schema")
class CollectionFields(MethodView):
    @landing_bp.response(200)
    def get(self):
        return {"endpoint": "collection", "fields": get_field_details(CollectionSchema)} """
