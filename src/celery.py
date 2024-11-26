from celery import Celery
from src.endpoint.media.media_types import MediaType

celery = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")  # Create a Celery instance

class CeleryTasks:
    @classmethod
    def init_celery(cls, app):
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
        return celery

    @celery.task(bind=True)
    def exec_generate_preview(cls, media_id, media_path, preview_path, type):
        from src.endpoint.media.models import MediaModel
        media = MediaModel.get(media_id)
        if media:
            print(f"from celery: abs Path: {media.absolute_path()}")
        from .utils.image_thumbnail import create_image_thumbnail
        from .utils.video_thumbnail import create_video_thumbnail4x4
        if type == MediaType.VIDEO:
            create_video_thumbnail4x4(media_path, preview_path)
            return f"preview generated for {media_id}, {type}"
        if type == MediaType.IMAGE:
            create_image_thumbnail(media_path, preview_path)
            return f"preview generated for {media_id}, {type}"
        return f"unsupported media type for {media_id}, {type}"
    
    