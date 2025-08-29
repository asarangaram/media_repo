import eventlet

eventlet.monkey_patch() 

from src.celery_app import CeleryTasks  # noqa: E402
from src.app_factory import create_app  # noqa: E402
from src.config import ConfigClass  # noqa: E402

app = create_app(ConfigClass)
CeleryTasks.init_celery(app)

if __name__ == "__main__":
    #app.run(host=ConfigClass.HOST_ADDR, port=ConfigClass.HOST_PORT, debug=True,  use_reloader = ConfigClass.USE_RELOADER) # Removed threaded=True, to make eventlet working
    eventlet.wsgi.server(
        eventlet.listen((ConfigClass.HOST_ADDR, int(ConfigClass.HOST_PORT))),
        app
    )
    
