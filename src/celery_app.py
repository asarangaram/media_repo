import os
from celery import Celery
from src.config import ConfigClass

from clmediakit import HLSStreamGenerator, HLSVariant


celery = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)  # Create a Celery instance


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
    def exec_generate_stream_lq(cls, media_id):
        from src.endpoint.entity.models import EntityModel

        return EntityModel.exec_generate_stream_lq(media_id=media_id)
