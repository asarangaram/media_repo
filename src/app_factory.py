# app_factory.py
import os
from celery import Celery
from flask import Flask

from src.celery import CeleryTasks
from src.endpoint.collection.model import CollectionModel
from src.endpoint.media.models import MediaModel

from .db import db
from .endpoint.landing.resources import landing_bp

# from .endpoint.image.resources import image_bp
from .endpoint.media.resources import create_media_resources, media_bp
from .endpoint.urlmap.resources import URL_map_resouce_bp
from .endpoint.collection.resources import collection_bp, create_collection_resources
from . import lock
from flask_migrate import Migrate
from sqlalchemy_continuum import version_class

from .endpoint.urlmap.resources import URLMapResource
from .endpoint.background.resources import background_task_bp
from .celery import celery


def create_app(config_object):
    if lock.instance_already_running(config_object):
        print("A instance is already accessing file storage")
        exit(-1)
    app = Flask(config_object.APP_NAME, template_folder=os.path.abspath("./src/html"))
    app.config.from_object(config_object)

    db.init_app(app)
    migrate = Migrate(app, db)
    db.configure_mappers()

    CollectionVersion = version_class(CollectionModel)
    MediaVersion = version_class(MediaModel)

    create_collection_resources(CollectionVersion)
    create_media_resources(MediaVersion)

    with app.app_context():
        db.create_all()

    URLMapResource.init_app(app)

    # Landing Page
    app.register_blueprint(landing_bp)
    # app.register_blueprint(image_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(URL_map_resouce_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(background_task_bp)

    return app
