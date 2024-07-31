from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound

class MediaProcessingException(UnsupportedMediaType):
    pass

# Change Type
class InternalImplementationError(InternalServerError):
    pass

class MediaNotFound (NotFound):
    pass