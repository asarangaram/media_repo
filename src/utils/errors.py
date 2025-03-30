from marshmallow import ValidationError
from werkzeug.exceptions import InternalServerError, NotFound


class MissingMD5Error(ValidationError):
    def __init__(self):
        super().__init__({"md5": ["md5 is required to create media"]})


class DuplicateItemError(ValidationError):
    def __init__(self, currentCollection, entity):
        super().__init__(
            {
                "collectionLabel": [
                    f"duplicate item found in {currentCollection.label}, with id {entity.id}."
                    ""
                ]
            }
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
        super().__init__("preview generation failed")


class MissingMediaFileError(NotFound):
    def __init__(self):
        super().__init__("media file not found")


class NoFileForCollectionError(NotFound):
    def __init__(self):
        super().__init__("can't attach file to Collection")


class MissingMediaError(NotFound):
    def __init__(self):
        super().__init__("media not found.")


class MissingMediaWhenUploadError(NotFound):
    def __init__(self):
        super().__init__("post media with a file.")


class VideoStreamError(InternalServerError):
    def __init__(self, id: int, additionalMessage=None):
        if additionalMessage:
            super().__init__(
                f"[Media #{id}]: Error while streaming media, {additionalMessage}"
            )
        else:
            super().__init__(f"[Media #{id}]: Error while streaming media")


class IncorrectUsageError(InternalServerError):
    def __init__(self):
        super().__init__(
            "Use create() or update() method to create or update a record."
        )
