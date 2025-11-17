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
                    f"Duplicate item found with id {entity.id}, "
                    f"parent: {entity.parent_id}"
                ),
            }
        )


class HardDeleteFailedError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "is_deleted": "failed to hard delete the entity, "
                "use soft delete first",
            }
        )


class MediaAlreadyDeleted(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "is_deleted": "media is already deleted. You can either "
                "restore or permanently delete",
            }
        )


class MediaMustHaveMediaFile(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "mediaFile": "media can't be created without a valid "
                "media file",
            }
        )


class CannotAttachFileWithCollectionError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "mediaFile": "Can't attach media file to Collection",
            }
        )


class ParentIDNotACollectionError(ValidationError):
    def __init__(self, parent_id: int):
        super().__init__(
            {"parent_id": f"parent_id {parent_id} is not a collection"}
        )


class ParentIDNotExistsError(ValidationError):
    def __init__(self, parent_id: int):
        super().__init__(
            {"parent_id": f"parent_id {parent_id} does not exist"}
        )


class ParentIDNotProvidedError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "parent_id": "parent_id not specified, "
                "unable to create default collection"
            }
        )


class EntityTypeDetectionError(ValidationError):
    def __init__(self):
        super().__init__(
            {
                "is_collection": "either is_collection should be "
                "specified OR a file must be present to know the entity type"
            }
        )


class MissingParametersInMatchQuery(ValidationError):
    def __init__(self):
        super().__init__(
            {"empty": "One of 'id', 'md5', or 'label' must be provided"}
        )

class TooManyParametersInMatchQuery(ValidationError):
    def __init__(self):
        super().__init__(
            {"empty": "Too many parameters provided for match query. Use only one of 'id', 'md5', or 'label'"}
        )
