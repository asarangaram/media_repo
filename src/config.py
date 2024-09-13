# config.py
import os
from dotenv import load_dotenv

load_dotenv('.flaskenv')


def get_required_env_variable(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value


def check_path(path):
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    return os.path.exists(parent_dir)


def get_db_uri():
    try:
        use_mysql = get_required_env_variable('USE_MYSQL')
    except BaseException:
        use_mysql = False

    repo = get_required_env_variable('IMAGE_REPO_DB')
    if use_mysql:
        user = get_required_env_variable('IMAGE_REPO_DB_ADMIN')
        password = get_required_env_variable('IMAGE_REPO_DB_ADMIN_PW')
        return f"mysql+pymysql://{user}:{password}@localhost/{repo}"
    elif check_path(repo):
        return f"sqlite:///{repo}"
    else:
        raise ValueError(f"DB Parameters are not set properly")


class ConfigClass(object):
    APP_NAME = get_required_env_variable('APP_NAME')
    API_TITLE = APP_NAME
    API_VERSION = "v1"
    PROPAGATE_EXCEPTIONS = True

    try:
        SECRET_KEY = get_required_env_variable('FLASK_SECRET_KEY1')
    except BaseException:
        SECRET_KEY = 'Secret!'

    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_JSON_PATH = "api-spec.json"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    API_DEFAULT_MEDIATYPE = "application/json"

    # OPENAPI_VERSION = "3.0.3"
    # OPENAPI_URL_PREFIX = "/"
    # OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    # OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = get_db_uri()
    print(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File Save
    FILE_STORAGE_LOCATION = get_required_env_variable('FILE_STORAGE_LOCATION')
