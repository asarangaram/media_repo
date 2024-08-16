
from flask.views import MethodView
from flask_smorest import Blueprint




URL_map_resouce_bp = Blueprint( 'utils', 'utils', url_prefix='/utils')

@URL_map_resouce_bp.route('/urlmap')
class URLMapResource(MethodView):
    @classmethod
    def init_app(cls, app):
        cls.app = app

    def get(self):
        # Extract information from the app's url_map
        endpoints = [rule.endpoint for rule in self.app.url_map.iter_rules()]
        url_map_info = {'endpoints': endpoints}
        return url_map_info


