# config.py
import os
from dotenv import load_dotenv


dotenv_path = os.path.expanduser("~/.mediarepo")

if not load_dotenv(dotenv_path):
    raise Exception("failed to load environment")


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
    use_mysql = os.getenv("USE_MYSQL", "false").lower() in ("1", "true", "yes")
    
    repo = get_required_env_variable("IMAGE_REPO_DB")
    if use_mysql:
        user = get_required_env_variable("IMAGE_REPO_DB_ADMIN")
        password = get_required_env_variable("IMAGE_REPO_DB_ADMIN_PW")
        return f"mysql+pymysql://{user}:{password}@localhost/{repo}"
    elif check_path(repo):
        return f"sqlite:///{repo}"
    else:
        raise ValueError("DB Parameters are not set properly")


class ConfigClass(object):
    APP_NAME = get_required_env_variable("APP_NAME")
    SECRET_KEY = get_required_env_variable("FLASK_SECRET_KEY1")
    FILE_STORAGE_LOCATION = get_required_env_variable("FILE_STORAGE_LOCATION")
    # Create folder if not exists
    os.makedirs(FILE_STORAGE_LOCATION, exist_ok=True)
    HOST_ADDR=get_required_env_variable("HOST_ADDR")
    HOST_PORT=get_required_env_variable("HOST_PORT")
    USE_RELOADER=os.environ.get("USE_RELOADER", "false").lower() == "true"

    API_TITLE = APP_NAME
    API_VERSION = "v1"
    PROPAGATE_EXCEPTIONS = True
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
    
    STREAM_STORAGE_LOCATION = f"{FILE_STORAGE_LOCATION}/streams"

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    HNSW_IMAGE_LOOKUP_LOCATION = f"{FILE_STORAGE_LOCATION}/image_lookup.idx"
    HNSW_VIDEO_LOOKUP_LOCATION = f"{FILE_STORAGE_LOCATION}/video_lookup.idx"

    # Update after checking the service if its running
    HAS_CELERY = True

    DEFAULT_COLLECTION_LABEL = "Unclassified"
    GENERATE_STREAM_TASK = "generate_stream_lq"

    SESSION_STORAGE_LOCATION = f"{FILE_STORAGE_LOCATION}/sessions"

    
