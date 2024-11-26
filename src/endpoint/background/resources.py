from flask.views import MethodView
from flask_smorest import Blueprint

from src.endpoint.media.resources import mask_errors

from .schemas import BGTaskSchema
from .models import BackgroundTaskModel

background_task_bp = Blueprint("background_task_bp", __name__, url_prefix="/background")


@background_task_bp.route("/<int:media_id>")
class BackgroundTask(MethodView):
    
    @background_task_bp.response(200, BGTaskSchema)
    def post(cls, media_id: int):
        bgtask = BackgroundTaskModel.start(media_id=media_id)
        return bgtask

    
    @background_task_bp.response(200, BGTaskSchema)
    def get(cls, media_id: int):
        bgtask = BackgroundTaskModel.get(media_id=media_id)
        return bgtask
