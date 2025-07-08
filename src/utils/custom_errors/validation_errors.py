from marshmallow import ValidationError


class MD5MissingError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "md5": "md5 is required to create media",
            }
        )


class MD5DuplicateItemError(ValidationError):
    def __init__(self, entity, parent=None):
        super().__init__(
            {
                "md5": (
                    f"Duplicate item found with id {entity.id}" f", parent: {parent.id}"
                    if parent
                    else ""
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


class CannotAttachFileWithCollectionError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "media": "Can't attach file to Collection",
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

