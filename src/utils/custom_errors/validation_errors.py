from marshmallow import ValidationError


class MD5MissingError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "md5": "md5 is required to create media",
            }
        )


class MD5DuplicateItemError(ValidationError):
    def __init__(self, entity):
        super().__init__(
            {
                "md5": (
                    f"Duplicate item found with id {entity.id}" f", parent: {entity.parentId}"
                    
                ),
            }
        )


class HardDeleteFailedError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "isDeleted": "failed to hard delete the entity, use soft delete first",
            }
        )

class MediaAlreadyDeleted(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "isDeleted": "media is already deleted. You can either restore or permanently delete",
            }
        )

class MediaMustHaveMediaFile(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "mediaFile": "media can't be created without a valid media file",
            }
        )


class CannotAttachFileWithCollectionError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "mediaFile": "Can't attach media file to Collection",
            }
        )


class ParentIdValidationError(ValidationError):
    def __init__(self, message):
        super().__init__(
            {
                "parentId": message
            }
        )


class ParentIdNotACollectionError(ValidationError):
    def __init__(self, parentId:int):
        super().__init__(
            {
                "parentId": f" parentId {parentId} is not a collection"
            }
        )

class ParentIdNotExistsError(ValidationError):
    def __init__(self, parentId:int):
        super().__init__(
            {
                "parentId": f" parentId {parentId} does not exists"
            }
        )

class ParentIdNotProvidedError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "parentId": "parentId not specified, unable to create default collection"
            }
        )

class Failed2GetEntityTypeError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "isCollection": "either isCollection should be specified OR a file must be present to know the entity type"
            }
        )


