# Media Repo Internals

This document provides an overview of the internal workings of the Media Repo application.

## Core Technologies

- **Backend Framework:** Flask
- **Database:** SQLAlchemy with MySQL or SQLite
- **Asynchronous Tasks:** Celery with Redis
- **API:** Flask-Smorest for RESTful API with OpenAPI/Swagger documentation
- **Data Versioning:** SQLAlchemy-Continuum
- **Similarity Search:** HNSWlib

## Project Structure

The project is organized into the following main directories:

- `src/`: Contains the core application logic.
  - `endpoint/`: Defines the API endpoints.
    - `entity/`: Manages media entities (CRUD, search).
    - `upload/`: Handles file uploads.
    - `urlmap/`: Provides a map of all URLs.
    - `background/`: Manages background tasks.
    - `landing/`: Serves the main landing page.
  - `html/`: HTML templates.
  - `utils/`: Utility functions.
- `migrations/`: Database migration scripts.
- `test/`: Application tests.

## Application Flow

1. **Initialization:**
   - The application is started via `wsgi.py`.
   - `app_factory.py` creates the Flask application instance.
   - Configuration is loaded from `config.py` and environment variables.
   - The database and other extensions (Flask-Migrate, Flask-Smorest) are initialized.
   - API blueprints are registered.

2. **Request Handling:**
   - Incoming requests are routed to the appropriate endpoint based on the URL.
   - Endpoints are defined as Flask-Smorest Blueprints and MethodViews.
   - Business logic is handled within the endpoint resource classes.

3. **Database Interaction:**
   - The application uses SQLAlchemy as an ORM to interact with the database.
   - The primary database model is `EntityModel` (`src/endpoint/entity/models.py`), which represents a media file.
   - SQLAlchemy-Continuum is used to automatically track and version changes to `EntityModel`.

4. **File Storage:**
   - Uploaded files are stored in the location specified by the `FILE_STORAGE_LOCATION` environment variable.
   - HLS video streams are stored in the `STREAM_STORAGE_LOCATION`.

5. **Asynchronous Tasks:**
   - Celery is used for long-running tasks, such as generating HLS video streams.
   - Tasks are defined in `src/celery_app.py` and executed by a separate Celery worker process.
   - Redis is used as the message broker and result backend for Celery.

6. **Similarity Search:**
   - The application uses HNSWlib to create and search for similar images and videos.
   - The HNSW indices are stored in the `HNSW_IMAGE_LOOKUP_LOCATION` and `HNSW_VIDEO_LOOKUP_LOCATION`.

## Configuration

The application is configured through environment variables, which are loaded from a `.mediarepo` file in the user's home directory. Key configuration options include:

- `APP_NAME`: The name of the application.
- `FLASK_SECRET_KEY1`: The secret key for the Flask application.
- `FILE_STORAGE_LOCATION`: The directory where media files are stored.
- `UPLOAD_STORAGE_LOCATION`: The directory where uploaded files are temporarily stored.
- `HOST_ADDR`: The host address for the application.
- `HOST_PORT`: The port for the application.
- `USE_MYSQL`: Whether to use MySQL as the database.
- `IMAGE_REPO_DB`: The name of the database.
- `IMAGE_REPO_DB_ADMIN`: The database administrator username.
- `IMAGE_REPO_DB_ADMIN_PW`: The database administrator password.
