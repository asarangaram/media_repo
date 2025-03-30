from marshmallow import ValidationError
from werkzeug.exceptions import InternalServerError, NotFound


class MissingMD5Error(ValidationError):
    def __init__(self):
        super().__init__("md5 is required to create media")


class DuplicateItemError(ValidationError):
    def __init__(self, entity, parent=None):
        super().__init__(
            f"Duplicate item found with id {entity.id}" f", parent: {parent.id}"
            if parent
            else "" "."
        )


class HardDeleteFailedError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "isDeleted": [
                    "failed to hard delete the entity, use soft delete first."
                ],
            }
        )


class PreviewGenerationFailedError(NotFound):
    def __init__(self):
        super().__init__("Preview generation failed")


class MissingMediaFileError(NotFound):
    def __init__(self):
        super().__init__("Media file not found")


class NoFileAcceptedForCollectionError(NotFound):
    def __init__(self):
        super().__init__("Can't attach file to Collection")


class NoFileForCollectionError(NotFound):
    def __init__(self):
        super().__init__("No file associated with Collection")


class MissingMediaError(NotFound):
    def __init__(self):
        super().__init__("Media not found.")


class MissingMediaWhenUploadError(NotFound):
    def __init__(self):
        super().__init__("Post media with a file.")


class VideoStreamError(NotFound):
    def __init__(self, additionalMessage):
        super().__init__(f"Error while streaming media. {additionalMessage}")


class IncorrectUsageError(InternalServerError):
    def __init__(self):
        super().__init__(
            "Use create() or update() method to create or update a record."
        )
