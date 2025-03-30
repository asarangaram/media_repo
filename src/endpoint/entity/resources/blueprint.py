from functools import wraps
from flask import request
from flask_smorest import Blueprint
from werkzeug.exceptions import InternalServerError, NotFound


entity_bp = Blueprint("entity_bp", __name__, url_prefix="/entity")
enableLogging = False


def mask_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if enableLogging:
            form_data = request.form.to_dict()
            print(f"Incoming Request Data: {form_data}")
        try:
            return func(*args, **kwargs)
        except NotFound:
            raise
        except Exception as e:
            raise InternalServerError(f"{e}")

    return wrapper
