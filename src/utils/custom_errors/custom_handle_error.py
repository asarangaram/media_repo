from flask import request
from marshmallow import ValidationError


from collections import OrderedDict
from functools import wraps

enableLogging = False


def custom_handle_error(func):
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
