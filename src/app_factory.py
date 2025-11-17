import os
from flask import Flask
from flask_migrate import Migrate
from sqlalchemy_continuum import version_class
from flask_smorest import Blueprint

from src.endpoint.upload.resources import register_sessions_resources


from .db import db
from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources.register_resources import register_resources
from src.endpoint.landing.resources import landing_bp
from src.endpoint.urlmap.resources import URL_map_resouce_bp
from src import lock
from src.endpoint.urlmap.resources import URLMapResource
from src.endpoint.background.resources import background_task_bp


def create_app(config_object):
    if lock.instance_already_running(config_object):
        print("A instance is already accessing file storage")
        exit(-1)
    app = Flask(config_object.APP_NAME, template_folder=os.path.abspath("./src/html"))
    app.config.from_object(config_object)

    db.init_app(app)
    migrate = Migrate(app, db, directory="src/migrations")  # noqa: F841
    db.configure_mappers()

    EntityVersion = version_class(EntityModel)
    

    entity_bp = Blueprint("entity_bp", __name__, url_prefix="/entity")
    register_resources(EntityVersion, entity_bp)

    session_bp = Blueprint("session_bp", __name__, url_prefix="/sessions")
    register_sessions_resources(session_bp)

    with app.app_context():
        db.create_all()

    URLMapResource.init_app(app)

    # Landing Page
    app.register_blueprint(landing_bp)
    app.register_blueprint(URL_map_resouce_bp)
    app.register_blueprint(entity_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(background_task_bp)

    return app
