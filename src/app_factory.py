# app_factory.py
import os
from flask import Flask

from .db import db
from .endpoint.entity.models import EntityModel
from .endpoint.entity.resources import create_entity_resources, entity_bp


from .endpoint.landing.resources import landing_bp
from .endpoint.urlmap.resources import URL_map_resouce_bp

from . import lock
from flask_migrate import Migrate
from sqlalchemy_continuum import version_class

from .endpoint.urlmap.resources import URLMapResource
from .endpoint.background.resources import background_task_bp


def create_app(config_object):
    if lock.instance_already_running(config_object):
        print("A instance is already accessing file storage")
        exit(-1)
    app = Flask(config_object.APP_NAME, template_folder=os.path.abspath("./src/html"))
    app.config.from_object(config_object)

    db.init_app(app)
    migrate = Migrate(app, db)
    db.configure_mappers()

    EntityVersion = version_class(EntityModel)

    create_entity_resources(EntityVersion)

    with app.app_context():
        db.create_all()

    URLMapResource.init_app(app)

    # Landing Page
    app.register_blueprint(landing_bp)
    app.register_blueprint(URL_map_resouce_bp)

    app.register_blueprint(entity_bp)
    app.register_blueprint(background_task_bp)

    return app
