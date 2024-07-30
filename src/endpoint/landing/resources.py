from flask.views import MethodView
from flask_smorest import Blueprint, abort

from .models import LandingPageModel
from .schemas import  LandingPageResultSchema

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

