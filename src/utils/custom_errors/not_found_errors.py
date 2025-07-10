from werkzeug.exceptions import NotFound


class MissingMediaFileError(NotFound):
    def __init__(self):
        super().__init__("Media file not found")


class MissingMediaError(NotFound):
    def __init__(self):
        super().__init__("Media not found.")


class MissingMediaWhenUploadError(NotFound):
    def __init__(self):
        super().__init__("Post media with a file.")


class VideoStreamError(NotFound):
    def __init__(self, additionalMessage):
        super().__init__(f"Error while streaming media. {additionalMessage}")
