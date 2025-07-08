from src.app_factory import create_app
from src.celery_app import CeleryTasks, celery
from src.config import ConfigClass


app = create_app(ConfigClass)

CeleryTasks.init_celery(app)
