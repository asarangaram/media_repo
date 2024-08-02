# wsgi.py

from flask import json, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import UnprocessableEntity
from flask_smorest import Api
from marshmallow import ValidationError

from .app_factory import create_app
from .config import ConfigClass

app = create_app(ConfigClass)


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


""" @app.errorhandler(Exception)
def handle_validation_error(error):
    print("reported validation error")
    return {
        "error": "Validation Error",
        "message": "; ".join([f"{field}: {'; '.join(messages)}" for field, messages in error.messages.items()]),
        "details": error.messages
    }, 422 """



""" if __name__ == "__main__":
    app.run(
        debug=True,
    ) """
