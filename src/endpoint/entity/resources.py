"""
This module defines the routes and handlers for managing media entities in the application.
It includes functionality for creating, retrieving, updating, deleting, and streaming media files.
"""

from collections import OrderedDict
from functools import wraps
from typing import Optional
from flask import (
    request,
)
from flask_smorest import Blueprint

from marshmallow import ValidationError
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
        except Exception as err:
            response = OrderedDict()
            response["type"] = type(err).__name__  # e.g. "ValueError"
            if isinstance(err, ValidationError):
                response["error"] = str(err.messages["_schema"])
                response["code"] = 422
            else:
                response["error"] = str(err)
                response["code"] = 500

            return response, response["code"]

    return wrapper


@entity_bp.errorhandler(404)
def not_found_error(error):
    """
    Handles 404 errors with a consistent JSON response.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and status code.
    """
    response = {
        "error": error.description,  # Default error message
        "status_code": 404,
    }
    return response, 404
