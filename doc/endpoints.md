# Media Repo Endpoints

This document outlines the API endpoints for the Media Repo application.

## Landing Page

- **`GET /`**: Displays the landing page with a list of recently added collections and media items.

## Entity Management

The `/entity` prefix is used for all entity-related endpoints.

### Create

- **`POST /entity/create`**: Creates a new media entity or collection.
  - **Request Body (form-data):**
    - `label` (string, required): The label for the entity.
    - `isCollection` (boolean, optional): Set to `true` to create a collection.
    - `media` (file, optional): The media file to upload. Required if `isCollection` is not `true`.
  - **Response:** The created entity object.

### Read

- **`GET /entity/all`**: Retrieves a list of all media entities. Supports filtering and pagination.
- **`GET /entity/match`**: Searches for an entity by `id`, `md5`, or `label`.
- **`GET /entity/<int:entity_id>`**: Retrieves a specific media entity by its ID.
- **`GET /entity/<int:entity_id>/download/media`**: Downloads the media file for a specific entity.
- **`GET /entity/<int:entity_id>/download/preview`**: Downloads the preview image for a specific entity.

### Update

- **`PUT /entity/<int:entity_id>/update`**: Updates an existing media entity.
  - **Request Body (form-data):**
    - `label` (string, optional): The new label for the entity.
    - `media` (file, optional): A new media file to replace the existing one.

### Delete

- **`PUT /entity/<int:entity_id>/to_bin`**: Soft-deletes a media entity (moves it to the bin).
- **`PUT /entity/<int:entity_id>/restore`**: Restores a soft-deleted media entity.
- **`DELETE /entity/<int:entity_id>/delete`**: Permanently deletes a media entity.
- **`DELETE /entity/reset`**: Deletes all entities. **Note:** This is only available on `darwin` systems for testing purposes.

### Upload Form

- **`GET /entity/upload`**: Displays an HTML form for uploading media files.

## File Uploads

The `/sessions` prefix is used for file upload endpoints.

- **`POST /sessions/<string:session_id>/upload`**: Uploads a media file for a given session.
  - **Request Body (form-data):**
    - `media` (file, required): The media file to upload.
  - **Response:** Information about the uploaded file.

## Background Tasks

The `/background` prefix is used for managing background tasks.

- **`POST /background/<int:media_id>`**: Starts all background tasks for a specific media ID (e.g., generating HLS streams).
- **`GET /background/<int:media_id>`**: Retrieves the status of all background tasks for a specific media ID.

## Video Streaming

- **`GET /entity/<int:entity_id>/stream/m3u8`**: Retrieves the M3U8 playlist for HLS streaming.
- **`GET /entity/<int:entity_id>/stream/<string:filename>`**: Retrieves a video segment (`.ts` file) or a playlist (`.m3u8` file).

## Utilities

- **`GET /utils/urlmap`**: Returns a map of all available API endpoints.
