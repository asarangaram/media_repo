from datetime import datetime
from typing import Optional, List, Any

import mimetypes
import os
import shutil
import sqlite3
import copy

import tempfile
import time

from clmediakit import (
    create_image_thumbnail,
    create_video_thumbnail4x4,
    MediaType,
    HLSStreamGenerator,
    HLSVariant,
)

from src.hnsw_indices import hnsw_image_lookup, hnsw_video_lookup
from src.endpoint.background.models import BackgroundTaskModel
from src.utils.custom_errors.validation_errors import (MD5MissingError, MD5DuplicateItemError, HardDeleteFailedError, CannotAttachFileWithCollectionError, ParentIdNotACollectionError, ParentIdNotExistsError, ParentIdNotProvidedError) 
from src.utils.custom_errors.internal_server_errors import (IncorrectUsageError, PreviewGenerationFailedError, IntegrityError,UnexpectedFailure)
from src.utils.custom_errors.not_found_errors import (MissingMediaFileError, MissingMediaError,MissingMediaWhenUploadError, VideoStreamError)

from ...db import db
from ...config import ConfigClass


class EntityModelReaderMixin:
    """
    A mixin class providing utility methods for reading entity instances from the database.
    Includes methods to retrieve a single entity or all entities with optional filtering.
    """

    @classmethod
    def get(cls, **kwargs: Any) -> Optional["EntityModel"]:
        items = cls.get_all(**kwargs)
        return items[0] if items else None

    @classmethod
    def get_all(cls, **kwargs: Any) -> List["EntityModel"]:
        """
        Retrieve all entity instances.
        Optionally filter by entity types.
        """
        if len(kwargs) == 0:
            items = cls.query.all()
        else:
            filters = {
                getattr(cls, key): kwargs[key]  # Convert key string to model attribute
                for key in kwargs
                if key in cls.__table__.columns
            }

            # Handle parentId being 0 as None
            if cls.parentId in filters and filters[cls.parentId] == 0:
                filters[cls.parentId] = None

            # Use *filters to unpack expressions
            items = cls.query.filter(
                *[col == val for col, val in filters.items()]
            ).all()

        return items


class EntityModel(db.Model, EntityModelReaderMixin):
    """
    Represents an entity in the database.
    Handles metadata, file storage, preview generation, and other entity-related operations.
    """

    __private_key = object()
    __versioned__ = {}

    __tablename__ = "entities"
    id = db.Column(db.Integer, primary_key=True)
    addedDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)
    isCollection = db.Column(db.Boolean)

    # Mandatory for Collections, Optional for Files
    label = db.Column(db.UnicodeText, nullable=True)
    parentId = db.Column(
        db.Integer,
        db.ForeignKey("entities.id"),
        nullable=True,
    )

    # Optional for Collections and Media
    description = db.Column(db.UnicodeText, nullable=True)

    # Mandatory for Media, should be set to None for Collections
    FileSize = db.Column(db.Integer, nullable=True)
    md5 = db.Column(db.String, unique=True, nullable=True)
    MIMEType = db.Column(db.String, nullable=True)
    type = db.Column(db.String, nullable=True)
    extension = db.Column(db.String, nullable=True)

    # Optional only for Media, should be set to None for Collections
    CreateDate = db.Column(db.DateTime, nullable=True)
    dHash = db.Column(db.String, nullable=True)
    ImageHeight = db.Column(db.Integer, nullable=True)
    ImageWidth = db.Column(db.Integer, nullable=True)
    Duration = db.Column(db.Float, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("label", "isCollection", name="unique_label_Collection"),
        db.CheckConstraint(
            "isCollection = 1 OR parentId IS NOT NULL",
            name="check_parent_not_null_if_not_collection",
        ),
        db.CheckConstraint(
            "isCollection = 1 OR FileSize IS NOT NULL",
            name="check_file_size_not_null_if_not_collection",
        ),
        db.CheckConstraint(
            "isCollection = 1 OR md5 IS NOT NULL",
            name="check_md5_not_null_if_not_collection",
        ),
        db.CheckConstraint(
            "isCollection = 1 OR MIMEType IS NOT NULL",
            name="check_mime_type_not_null_if_not_collection",
        ),
        db.CheckConstraint(
            "isCollection = 1 OR type IS NOT NULL",
            name="check_type_not_null_if_not_collection",
        ),
        db.CheckConstraint(
            "isCollection = 1 OR extension IS NOT NULL",
            name="check_extension_not_null_if_not_collection",
        ),
    )
    # remove  uselist=True,?
    task = db.relationship("BackgroundTaskModel", uselist=True, backref="entities")
    not_modifiable_columns = ["id", "addedDate", "updatedDate", "isCollection"]

    def __init__(self, private_key: Optional[object] = None, **kwargs: Any) -> None:
        if private_key != EntityModel.__private_key:
            raise IncorrectUsageError()
        derived = {}
        if kwargs.get("MIMEType"):
            derived["type"] = MediaType.from_mime(kwargs.get("MIMEType"))
            derived["extension"] = mimetypes.guess_extension(kwargs.get("MIMEType"))
            if not derived["extension"]:
                derived["extension"] = ".bin"

        super().__init__(
            **{key: kwargs[key] for key in kwargs if key in self.__table__.columns},
            **derived,
        )

    def delete_from_db(self) -> None:
        """
        Delete the current entity instance from the database.
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, **kwargs: Any) -> "EntityModel":
        """
        Create a new entity instance.
        Handles parent validation, duplicate checks, and default parent creation for media.
        """

        ## check if the parent exists and it is a collection
        parentId = kwargs.get("parentId")

        parent = cls.get(id=parentId) if parentId else None

        if parent:
            if not parent.isCollection:
                raise ParentIdNotACollectionError(parentId)

        if parentId and not parent:
            raise ParentIdNotExistsError(parentId)

        ## if no parent and its a media, try creating a default parent
        parentArg = {}
        if not parent and not kwargs.get("isCollection"):
            parent = cls.get(label=ConfigClass.DEFAULT_COLLECTION_LABEL)
            if not parent:
                parent = EntityModel.create(
                    **{"isCollection": 1, "label": ConfigClass.DEFAULT_COLLECTION_LABEL}
                )
            if not parent:
                raise ParentIdNotProvidedError(
                    
                )
            parentArg = {"parentId": parent.id}

        ## Check for duplicate
        if kwargs.get("isCollection"):
            if duplicate := cls.get(label=kwargs.get("label")):
                if (
                    kwargs.get("parentId")
                    and kwargs.get("parentId") != duplicate.parentId
                ):
                    raise MD5DuplicateItemError(duplicate, parent=parent)
                return duplicate
        else:
            if kwargs.get("md5") is None:
                raise MD5MissingError()
            if duplicate := cls.get(md5=kwargs.get("md5")):
                # FIXME: when the item is present in another 
                # collection, for now, we ignore the update 
                # but what if the user's intention is to move ?
                # to the recent update? Need to define a mechanism for this
                """ if (
                    kwargs.get("parentId")
                    and kwargs.get("parentId") != duplicate.parentId
                ):
                    raise MD5DuplicateItemError(duplicate, parent=parent) """
                return duplicate

        # Create and accept
        try:
            entity = EntityModel(private_key=cls.__private_key, **kwargs, **parentArg)
            if cls.acceptEntity(entity, filepath=kwargs.get("filepath")):
                if not entity.isCollection:
                    if entity.type == MediaType.VIDEO:
                        hnsw_video_lookup.add(entity.id, entity.dHash)
                    elif entity.type == MediaType.IMAGE:
                        hnsw_image_lookup.add(entity.id, entity.dHash)
                return entity
            raise UnexpectedFailure()
        except Exception as e:
            raise

    @classmethod
    def update(cls, _id: int, **kwargs: Any) -> "EntityModel":
        """
        Update an existing entity instance with new metadata or attributes.
        If the updated entity is a duplicate, raise a MD5DuplicateItemError.
        """
        try:
            duplicate = None
            if kwargs.get("md5"):
                if duplicate := cls.get(md5=kwargs.get("md5")):
                    if duplicate.id != _id:
                        ## if file is present already in the db with different id
                        ## we can't update the current item, as its a conflict.
                        raise MD5DuplicateItemError()
            if duplicate:
                currentEntity = duplicate
            else:
                currentEntity = cls.get(id=_id)
            if not currentEntity:
                raise MissingMediaError()
            updatedEntity = copy.deepcopy(currentEntity)
            
            for key, value in kwargs.items():
                    if (
                        key in updatedEntity.__table__.columns
                        and key not in cls.not_modifiable_columns
                    ):
                        if getattr(updatedEntity, key) != value:
                            setattr(updatedEntity, key, value)
                            
            # Nothing changed.
            if cls.acceptEntity(
                    updatedEntity, currentEntity, filepath=kwargs.get("filepath")
                ):
                    if not updatedEntity.isCollection:
                        if updatedEntity.type == MediaType.VIDEO:
                            hnsw_video_lookup.replace(updatedEntity.id, updatedEntity.dHash)
                        elif updatedEntity.type == MediaType.IMAGE:
                            hnsw_image_lookup.replace(updatedEntity.id, updatedEntity.dHash)
                    return updatedEntity
            return currentEntity
        except Exception as e:
            raise
        

    def __eq__(self, other: Any) -> bool:
        """
        Compare two entity instances for equality based on their attributes.
        Excludes addedDate and updatedDate from the comparison.
        """
        if not isinstance(other, self.__class__):
            return False
        return all(
            getattr(self, column.name) == getattr(other, column.name)
            for column in self.__table__.columns
            if column.name not in ["addedDate", "updatedDate"]
        )

    @property
    def filename(self) -> str:
        """
        Generate the relative filename for the entity based on its content type and MD5 hash.
        """
        return os.path.join(self.MIMEType, f"{str(self.md5)}{self.extension}")

    @property
    def preview_filename(self) -> str:
        """
        Generate the filename for the entity's preview image.
        """
        return f"{self.filename}.tn.jpeg"

    @property
    def absolute_filename(self) -> str:
        """
        Get the absolute path to the entity file in the storage location.
        """
        return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.filename)

    @property
    def absolute_preview_filename(self) -> str:
        """
        Get the absolute path to the entity's preview image in the storage location.
        """
        return f"{self.absolute_filename}.tn.jpeg"

    def get_preview(self) -> str:
        """
        Retrieve the preview image for the entity.
        Generate the preview if it does not already exist.
        """
        if not os.path.exists(self.absolute_filename):
            raise MissingMediaFileError()

        if not os.path.exists(
            absolute_preview_filename := self.absolute_preview_filename
        ):
            self.generate_preview(self.absolute_filename, absolute_preview_filename)
        if os.path.exists(absolute_preview_filename):
            return absolute_preview_filename
        else:
            raise PreviewGenerationFailedError()

    def generate_preview(self, path: str, preview: str) -> None:
        """
        Generate a preview image or video thumbnail for the entity.
        """
        try:
            if self.type == MediaType.VIDEO:
                create_video_thumbnail4x4(path, preview)
            elif self.type == MediaType.IMAGE:
                create_image_thumbnail(path, preview)
            return
        except Exception as e:
            raise PreviewGenerationFailedError() from e

    @classmethod
    def acceptEntity(
        cls,
        curr: "EntityModel",
        prev: Optional["EntityModel"] = None,
        filepath: Optional[str] = None,
    ) -> bool:
        """
        Validate and accept changes to an entity instance.
        Handles database updates, media file management, and error handling.
        """
        try:
            if curr != prev:
                timenow = datetime.now()
                curr.addedDate = prev.addedDate if prev else timenow
                curr.updatedDate = timenow
                

                db.session.flush()
                try:
                    if prev is None:
                        db.session.add(curr)
                    else:
                        db.session.merge(curr)

                    if not curr.isCollection:
                        prev_media = prev.absolute_filename if prev else None
                        curr_media = curr.absolute_filename
                        if curr_media != prev_media:  # different file or new file
                            if not filepath:
                                raise MissingMediaWhenUploadError()

                            curr.acceptMedia(filepath=filepath)

                            if curr_media != prev_media and prev:
                                prev.removeMedia()

                    db.session.commit()
                except sqlite3.IntegrityError as e:
                    raise IntegrityError(e)
                
                except Exception as e:
                    raise Exception("Unexpected error occurred") from e
            return curr != prev
        except Exception as e:
            db.session.rollback()
            prev_media = prev.absolute_filename if prev else None
            curr_media = curr.absolute_filename
            if curr_media != prev_media:
                curr.removeMedia()
            raise

    def acceptMedia(
        self, overwrite: bool = True, filepath: Optional[str] = None
    ) -> None:
        """
        Accept and store the media file associated with the entity.
        Generates a preview for the media.
        """
        path = self.absolute_filename
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(filepath, path)
        self.generate_preview(path, self.absolute_preview_filename)

    def removeMedia(self) -> None:
        """
        Remove the media file and its preview associated with the entity.
        """
        if os.path.exists(self.absolute_filename):
            os.remove(self.absolute_filename)
        if os.path.exists(self.absolute_preview_filename):
            os.remove(self.absolute_preview_filename)

    @classmethod
    def delete(cls, _id: int) -> None:
        """
        Delete an entity instance by its ID.
        Raise HardDeleteFailedError if the entity is not marked as deleted.
        """
        result_map  = {"id": _id}
        try:
            result_map["status"] =  "not deleted", 
            entity = cls.get(id=_id)
            if not entity:
                result_map["error"] = f"no item found with id {_id}"
                return result_map, 404
            if not entity.isDeleted:
                result_map["error"] = "failed to hard delete the entity, use soft delete first."
                return result_map, 409
                

            path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, entity.path)
            if os.path.exists(path):
                os.remove(path)

            if entity.type == MediaType.VIDEO:
                hnsw_video_lookup.remove(entity.id)
            elif entity.type == MediaType.IMAGE:
                hnsw_image_lookup.remove(entity.id)

            entity.delete_from_db()
            print("Deleted successfully")
            result_map["status"] =  "deleted", 
            return result_map, 200
        except Exception as e:
            result_map["error"] = f"Internal Server Error {e}"
            return result_map, 500
            

    @classmethod
    def delete_all(cls) -> None:
        """
        Delete all entity instances from the database.
        """
        all = cls.query.all()
        for entity in all:
            if not entity.isDeleted:
                cls.delete(entity.id)

    @classmethod
    def wait_for_m3u8(cls, id: int, master_pl: str, timeout: int = 60) -> None:
        """
        Wait for the adaptive.m3u8 file to be created within the specified timeout.
        Raise VideoStreamError if the timeout is exceeded.
        """
        start_time = time.time()
        while not os.path.exists(master_pl):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise VideoStreamError(
                    additionalMessage=f"background task not responding "
                    "for media {id}",
                )
            time.sleep(1)  # Poll every second
        return

    def get_stream_folder(self) -> str:
        """
        Retrieve the folder containing the media's video stream.
        If the stream does not exist, initiate its generation.
        """
        if self.type != MediaType.VIDEO:
            raise VideoStreamError(
                additionalMessage=f"Media with id {self.id} is "
                f"a {self.type} (MIME: {self.MIMEType}), not a video",
            )
        stream_path = os.path.join(self.MIMEType, f"media_{str(self.id)}")
        output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
        master_pl = os.path.join(output_dir, "adaptive.m3u8")
        if not os.path.exists(master_pl):
            if ConfigClass.HAS_CELERY:
                BackgroundTaskModel.start(self.id, ConfigClass.GENERATE_STREAM_TASK)
                self.wait_for_m3u8(id=self.id, master_pl=master_pl)
            else:
                EntityModel.exec_generate_stream_lq(self.id)

        return output_dir

    @classmethod
    def exec_generate_stream_lq(cls, media_id: int) -> str:
        """
        Generate a low-quality HLS stream for the specified media ID.
        """
        media = EntityModel.get(id=media_id)
        if media:
            if media.type != MediaType.VIDEO:
                return (
                    f"Can't stream . media_{media.id}:not a video. type: {media.type}"
                )
            input_file = media.absolute_filename
            stream_path = os.path.join(media.MIMEType, f"media_{str(media.id)}")

            output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
            os.makedirs(os.path.dirname(output_dir), exist_ok=True)
            master_pl = os.path.join(output_dir, "adaptive.m3u8")
            if os.path.exists(master_pl):
                return f"media_{str(media.id)}: master_pl exists. not regenerating"
            generator = HLSStreamGenerator(
                input_file=input_file,
                output_dir=output_dir,
            )

            try:
                valid = generator.addVariants([HLSVariant(resolution=240, bitrate=200)])

            except Exception as e:
                # FIXME: delete generated files if it fails
                valid = False
            if not valid:
                return f"media_{str(media.id)}: failed to generate stream"
            return f"media_{str(media.id)}: stream generated"
        return f"media_{str(media.id)}: media not found"


class TempFile:
    """
    A utility class for managing temporary files.
    Ensures unique filenames and provides cleanup functionality.
    """

    def __init__(self, file: Any) -> None:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)

        # Avoid overwriting by adding a number if file exists
        base, ext = os.path.splitext(temp_path)
        counter = 1
        while os.path.exists(temp_path):
            temp_path = f"{base}_{counter}{ext}"
            counter += 1
        file.save(temp_path)
        self.path = temp_path

    def remove(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
