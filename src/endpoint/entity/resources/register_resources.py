from src.endpoint.entity.resources.blob_resources import (
    blob_download_media,
    blob_download_preview,
    blob_download_video_stream,
)

from src.endpoint.entity.resources.create_resources import \
    entity_create_resource
from src.endpoint.entity.resources.upload_form import entity_upload_form
from src.endpoint.entity.resources.read_resources import (
    entity_match_resource,
    entity_read_all_resource,
    entity_read_resource,
)
from src.endpoint.entity.resources.update_resources import \
    entity_update_resource

from src.endpoint.entity.resources.delete_resources import (
    entity_softdelete_resource,
    entity_softrestore_resource,
    entity_harddelete_resource,
    reset_resource,
)


def register_resources(
    MediaVersion, route, canModify=True, canDelete=True
):
    """
    Registers routes and handlers for media-related operations.

    Args:
        MediaVersion: The SQLAlchemy model representing media versions.
    """

    entity_read_all_resource(MediaVersion, route)
    entity_read_resource(MediaVersion, route)
    entity_match_resource(MediaVersion, route)

    blob_download_media(MediaVersion, route)
    blob_download_preview(MediaVersion, route)
    blob_download_video_stream(MediaVersion, route)

    if canModify:
        entity_create_resource(MediaVersion, route)
        entity_update_resource(MediaVersion, route)
        entity_upload_form(MediaVersion, route)

    if canDelete:
        entity_softdelete_resource(MediaVersion, route)
        entity_softrestore_resource(MediaVersion, route)
        entity_harddelete_resource(MediaVersion, route)
        #  Only on test Server
        reset_resource(MediaVersion, route)
