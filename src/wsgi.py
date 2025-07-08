from flask import jsonify
from werkzeug.exceptions import UnprocessableEntity
from src.celery import CeleryTasks


from .app_factory import create_app
from .config import ConfigClass

app = create_app(ConfigClass)
CeleryTasks.init_celery(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
