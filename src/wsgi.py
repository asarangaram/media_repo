# wsgi.py

from sqlite3 import IntegrityError
from flask import json, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import UnprocessableEntity, InternalServerError
from flask_smorest import Api
from marshmallow import ValidationError

from .app_factory import create_app
from .config import ConfigClass

app = create_app(ConfigClass)


@app.errorhandler(IntegrityError)
def handle_integrity_error(e):
    return jsonify({"error": "Database integrity error occurred"}), 400

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # Start with the correct headers and status code from the error
    response = e.get_response()
    # Replace the body with JSON
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


""" @app.errorhandler(404)
def not_found_error(e):
    response = {"message": str(error)}
    return jsonify(response), 404 """


@app.errorhandler(UnprocessableEntity)
def handle_unprocessable_entity(e):
    # Get the original ValidationError raised by marshmallow
    headers = e.data.get("headers", None)
    messages = e.data.get("messages", ["Invalid request."])

    if headers:
        return (
            jsonify({"code": e.code, "name": e.name, "description": messages}),
            e.code,
            headers,
        )
    else:
        return jsonify({"errors": messages}), e.code

@app.errorhandler(InternalServerError)
def internalservererror(e):
    return jsonify({"error": e.description}), e.code

@app.errorhandler(TypeError)
def typerror(e):
    return jsonify({"error": e}), 500



@app.errorhandler(Exception)
def handle_validation_error(error):
    try:
        message = "; ".join([f"{field}: {'; '.join(messages)}" for field, messages in error.messages.items()])
    except:
        message = error

    return {
        "error": "Validation Error",
        "message": message,
        # "details": error.messages
    }, 422


if __name__ == "__main__":
    app.run( 
        host='0.0.0.0', port=5000,
        debug=True, threaded=True
    )
