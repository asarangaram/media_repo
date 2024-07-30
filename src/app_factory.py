# app_factory.py
import os
from flask import Flask

from .db import db
from .endpoint.landing.resources import landing_bp
from .endpoint.image.resources import image_bp
from .endpoint.urlmap.resources import URL_map_resouce_bp
from . import lock
from flask_migrate import Migrate

from .endpoint.urlmap.resources import URLMapResource


def create_app(config_object):

    if lock.instance_already_running(config_object):
        print("A instance is already accessing file storage")
        exit(-1)
    app = Flask(config_object.APP_NAME,
                template_folder=os.path.abspath('./src/html'))
    app.config.from_object(config_object)

    db.init_app(app)
    migrate = Migrate(app, db)
    with app.app_context():
        db.create_all()

    URLMapResource.init_app(app)

    # Landing Page
    app.register_blueprint(landing_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(URL_map_resouce_bp)

    return app
