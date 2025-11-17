from werkzeug.exceptions import NotFound


class MissingMediaFileError(NotFound):
    def __init__(self):
        super().__init__("Media file not found")


class MissingMediaError(NotFound):
    def __init__(self):
        super().__init__("Media not found.")


class MissingMediaWhenUploadError(NotFound):
    def __init__(self):
        super().__init__("A file is required when creating or updating this media entity.")


class VideoStreamError(NotFound):
    def __init__(self, additionalMessage):
        super().__init__(f"Error while streaming media. {additionalMessage}")
