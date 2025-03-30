from datetime import datetime

import mimetypes
import os
import shutil
import sqlite3
from sqlalchemy.exc import IntegrityError
import tempfile
import time
import traceback

from clmediakit import (
    create_image_thumbnail,
    create_video_thumbnail4x4,
    MediaType,
    CLMetaData,
    HLSStreamGenerator,
    HLSVariant,
)
from marshmallow import ValidationError
from src.hnsw_indices import hnsw_image_lookup, hnsw_video_lookup
from src.endpoint.background.models import BackgroundTaskModel
from src.utils.errors import (
    DuplicateItemError,
    HardDeleteFailedError,
    IncorrectUsageError,
    MissingMD5Error,
    MissingMediaError,
    MissingMediaFileError,
    MissingMediaWhenUploadError,
    PreviewGenerationFailedError,
    VideoStreamError,
)

from ...db import db
from ...config import ConfigClass


class EntityModelReaderMixin:
    @classmethod
    def get(cls, **kwargs):
        items = cls.get_all(**kwargs)
        return items[0] if items else None

    @classmethod
    def get_all(cls, **kwargs):
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
    Represents a entity in the database.
    This model handles metadata, file storage, preview generation, and other entity-related operations.
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
    FileSize = db.Column(db.String, nullable=True)
    md5 = db.Column(db.String, unique=True, nullable=True)
    MIMEType = db.Column(db.String, nullable=True)
    type = db.Column(db.String, nullable=True)
    extension = db.Column(db.String, nullable=True)

    # Optional only for Media, should be set to None for Collections
    CreateDate = db.Column(db.DateTime, nullable=True)
    dHash = db.Column(db.String, nullable=True)
    ImageHeight = db.Column(db.Integer, nullable=True)
    ImageWidth = db.Column(db.Integer, nullable=True)
    Duration = db.Column(db.String, nullable=True)

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
    error_translator = {
        "check_parent_not_null_if_not_collection": "Media must have parentId",
        "check_file_size_not_null_if_not_collection": "Failed to detect file_size from media",
        "check_md5_not_null_if_not_collection": "Failed to calculate md5 from media",
        "check_mime_type_not_null_if_not_collection": "Failed to determine mime type from media",
        "check_type_not_null_if_not_collection": "Failed to determine type for media",
        "check_extension_not_null_if_not_collection": "Failed to determine extensio for media",
    }

    def __init__(self, private_key=None, **kwargs):
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

    def save_to_db(self):
        """Save the current entity instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """Delete the current entity instance from the database."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, **kwargs):

        ## check if the parent exists and it is a collection
        parentId = kwargs.get("parentId")

        parent = cls.get(id=parentId) if parentId else None

        if parent:
            if not parent.isCollection:
                raise ValidationError(f" parentId {parentId} is not a collection")

        if parentId and not parent:
            raise ValidationError(f" parentId {parentId} does not exists")

        ## if no parent and its a media, try creating a default parent
        parentArg = {}
        if not parent and not kwargs.get("isCollection"):
            parent = cls.get(label="Unclassified")
            if not parent:
                parent = EntityModel.create(
                    **{"isCollection": 1, "label": "Unclassified"}
                )
            if not parent:
                raise ValidationError(
                    "parentId not specified, unable to create default collection"
                )
            parentArg = {"parentId": parent.id}
            pass

        ## Check for duplicate
        if kwargs.get("isCollection"):
            if duplicate := cls.get(label=kwargs.get("label")):
                if (
                    kwargs.get("parentId")
                    and kwargs.get("parentId") != duplicate.parentId
                ):
                    raise DuplicateItemError(duplicate, parent=parent)
                return duplicate
        else:
            if kwargs.get("md5") is None:
                raise MissingMD5Error()
            if duplicate := cls.get(md5=kwargs.get("md5")):
                if (
                    kwargs.get("parentId")
                    and kwargs.get("parentId") != duplicate.parentId
                ):
                    raise DuplicateItemError(duplicate, parent=parent)
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
            ## This should not occur in create, as we either return True
            ## or generate exception
            raise ValidationError("Entity registration failed")
        except Exception as e:
            raise

    @classmethod
    def update(cls, _id, **kwargs):
        """
        Update an existing entity instance with new metadata or attributes.
        If the updated entity is a duplicate, raise a DuplicateItemError.
        """
        currentEntity = cls.get(_id)
        if currentEntity:
            raise MissingMediaError()
        updatedEntity = shutil.copy.deepcopy(currentEntity)

        not_modifiable_columns = ["id", "addedDate", "updatedDate", "isCollection"]

        for key, value in kwargs.items():
            if (
                key in updatedEntity.__table__.columns
                and key not in not_modifiable_columns
            ):
                if getattr(updatedEntity, key) != value:
                    setattr(updatedEntity, key, value)

        try:
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

    def __eq__(self, other):  # FIXME
        """
        Compare two entity instances for equality based on their attributes.
        """
        if not isinstance(other, self.__class__):
            return False
        return (
            self.id == other.id
            and self.label == other.label
            and self.collectionId == other.collectionId
            and self.ref == other.ref
            and self.isDeleted == other.isDeleted
            and self.CreateDate == other.CreateDate
            and self.FileSize == other.FileSize
            and self.ImageHeight == other.ImageHeight
            and self.ImageWidth == other.ImageWidth
            and self.Duration == other.Duration
            and self.MIMEType == other.MIMEType
            and self.dHash == other.dHash
            and self.md5 == other.md5
        )

    @property
    def filename(self):
        """Generate the relative filename for the entity based on its content type and MD5 hash."""
        return os.path.join(self.MIMEType, f"{str(self.md5)}{self.extension}")

    @property
    def preview_filename(self):
        """Generate the filename for the entity's preview image."""
        return f"{self.filename}.tn.jpeg"

    @property
    def absolute_filename(self):
        """Get the absolute path to the entity file in the storage location."""
        return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.filename)

    @property
    def absolute_preview_filename(self):
        """Get the absolute path to the entity's preview image in the storage location."""
        return f"{self.absolute_filename}.tn.jpeg"

    def get_preview(self):
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

    def generate_preview(self, path, preview):
        try:
            if self.type == MediaType.VIDEO:
                create_video_thumbnail4x4(path, preview)
            if self.type == MediaType.IMAGE:
                create_image_thumbnail(path, preview)
            return
        except Exception as e:
            raise PreviewGenerationFailedError()

    @classmethod
    def acceptEntity(cls, curr, prev=None, filepath=None):
        try:
            if curr != prev:
                timenow = datetime.now()
                curr.addedDate = prev.addedDate if prev else timenow
                curr.updatedDate = timenow
                db.session.flush()
                try:
                    db.session.add(curr)

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
                except (IntegrityError, sqlite3.IntegrityError) as e:
                    raised = False
                    for key, value in cls.error_translator.items():
                        if key in str(e):
                            raised = True
                            raise ValidationError(value)
                    if not raised:
                        raise
                except Exception as e:
                    raise Exception("Unexpected error occurred")
            return curr != prev
        except Exception as e:
            db.session.rollback()
            prev_media = prev.absolute_filename if prev else None
            curr_media = curr.absolute_filename
            if curr_media != prev_media:
                curr.removeMedia()
            raise

    def acceptMedia(self, overwrite=True, filepath=None):
        path = self.absolute_filename
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(filepath, path)
        self.generate_preview(path, self.absolute_preview_filename)

    def removeMedia(self):
        if os.path.exists(self.absolute_filename):
            os.remove(self.absolute_filename)
        if os.path.exists(self.absolute_preview_filename):
            os.remove(self.absolute_preview_filename)

    @classmethod
    def delete(cls, _id: int):
        """
        Delete a entity instance by its ID.
        Raise HardDeleteFailedError if the entity is not marked as deleted.
        """
        entity = cls.get(_id)
        if not entity.isDeleted:
            raise HardDeleteFailedError()

        path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, entity.path)
        if os.path.exists(path):
            os.remove(path)

        if entity.type == MediaType.VIDEO:
            hnsw_video_lookup.remove(entity.id)
        elif entity.type == MediaType.IMAGE:
            hnsw_image_lookup.remove(entity.id)

        entity.delete_from_db()

    @classmethod
    def delete_all(cls):
        """Delete all entity instances from the database."""
        all = cls.query.all()
        for entity in all:
            if not entity.isDeleted:
                cls.delete(entity.id)

    @classmethod
    def wait_for_m3u8(self, master_pl: str, timeout: int = 60):
        """
        Wait for the adaptive.m3u8 file to be created within the specified timeout.
        Return False if the timeout is exceeded.
        """
        start_time = time.time()
        while not os.path.exists(master_pl):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise VideoStreamError(
                    additionalMessage=f"background task not responding for media {self.id}",
                )
            time.sleep(1)  # Poll every second
        return

    def get_stream_folder(self):
        """
        Retrieve the folder containing the media's video stream.
        If the stream does not exist, initiate its generation.
        """
        if self.type != "video":  # why MediaType.VIDEO is not working?
            print(f"can't stream {self.id}. not a video")
            raise VideoStreamError(
                additionalMessage=f"Media with id {self.id} is "
                f"a {self.type} (MIME: {self.MIMEType}), not a video",
            )
        stream_path = os.path.join(self.MIMEType, f"media_{str(self.id)}")
        output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
        master_pl = os.path.join(output_dir, "adaptive.m3u8")
        if not os.path.exists(master_pl):
            RUN_IN_BACKGROUND = True

            if RUN_IN_BACKGROUND:
                BackgroundTaskModel.start(self.id, "generate_stream_lq")
                self.wait_for_m3u8(master_pl=master_pl)

            else:
                EntityModel.exec_generate_stream_lq(self.id)

        return output_dir

    @classmethod
    def exec_generate_stream_lq(cls, media_id):
        media = EntityModel.get(id=media_id)
        if media:
            if media.type != "video":  # why MediaType.VIDEO is not working?
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
            # HLSVariant(resolution=720, bitrate=900),
            # HLSVariant(resolution=480, bitrate=400),
            try:
                valid = generator.addVariants([HLSVariant(resolution=240, bitrate=200)])

            except Exception as e:
                # FIXME: WE may consider deleting if ffmpeg fails
                valid = False
            if not valid:
                return f"media_{str(media.id)}: failed to generate stream"
            return f"media_{str(media.id)}: stream generated"
        return f"media_{str(media.id)}: media not found"


class TempFile:
    def __init__(self, file):
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

    def remove(self):
        if os.path.exists(self.path):
            os.remove(self.path)
