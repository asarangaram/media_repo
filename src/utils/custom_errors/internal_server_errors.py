import sqlite3
from werkzeug.exceptions import InternalServerError


class IncorrectUsageError(InternalServerError):
    """
    This internal error is raised only when the developer try to call
    the __init__ of the model directly.
    """

    def __init__(self):
        super().__init__(
            "DEVERR: Use create() or update() method to create or update a record."
        )


class PreviewGenerationFailedError(InternalServerError):
    """
    In normal scenario, this error can't occur. This internal error
    is raised when the server has problem reading and writing into
    the disk or image encoder fails.
    """

    def __init__(self):
        super().__init__("DEVERR: Preview generation failed")


## This should not occur in create, as we either return True
## or generate exception


class UnexpectedFailure(InternalServerError):
    """
    In normal scenario, this error can't occur. this error is introduces
    only to guard the developer mistake in entity registration logic,
    and might occur if some error check is missing in the implementation
    """

    def __init__(self):
        super().__init__("DEVERR: This should not have happened. Fix it")

class DataNotLoadedError(InternalServerError):
    """
    In normal scenario, this error can't occur. this error is introduces
    only to guard the developer mistake in entity registration logic,
    and might occur if some error check is missing in the implementation
    """

    def __init__(self, message):
        super().__init__(f"DEVERR: {message}")

class IntegrityError(InternalServerError):
    """
    In normal scenario, this error can't occur. this error is introduces
    only to guard the developer mistake in data base access or not
    checking the fields before commiting to db.
    """

    error_translator = {
        "check_parent_not_null_if_not_collection": "Media must have parentId",
        "check_file_size_not_null_if_not_collection": "Failed to detect file_size from media",
        "check_md5_not_null_if_not_collection": "Failed to calculate md5 from media",
        "check_mime_type_not_null_if_not_collection": "Failed to determine mime type from media",
        "check_type_not_null_if_not_collection": "Failed to determine type for media",
        "check_extension_not_null_if_not_collection": "Failed to determine extensio for media",
    }

    def __init__(self, error: sqlite3.IntegrityError):
        found = False
        for key, value in self.error_translator.items():
            if key in str(error):
                super().__init__(value)
                found = True
        if not found:
            super().__init__(f"Unable to translate db error {str(error)}")
