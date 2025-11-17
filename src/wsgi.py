from src.celery_app import CeleryTasks
from src.app_factory import create_app
from src.config import ConfigClass

app = create_app(ConfigClass)
CeleryTasks.init_celery(app)

if __name__ == "__main__":
    app.run(
        host=ConfigClass.HOST_ADDR,
        port=ConfigClass.HOST_PORT,
        debug=True,
        threaded=True,
        use_reloader=ConfigClass.USE_RELOADER,
    )
