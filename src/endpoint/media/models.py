from datetime import datetime

import mimetypes
import os
import shutil
import tempfile
import time

from clmediakit import (
    create_image_thumbnail,
    create_video_thumbnail4x4,
    MediaType,
    CLMetaData,
)
from src.hnsw_indices import hnsw_image_lookup, hnsw_video_lookup
from src.endpoint.background.models import BackgroundTaskModel
from src.utils.errors import (
    DuplicateItemError,
    HardDeleteFailedError,
    IncorrectUsageError,
    MissingMD5Error,
    MissingMediaError,
    MissingMediaFileError,
    PreviewGenerationFailedError,
    VideoStreamError,
)

from ...db import db
from ...config import ConfigClass
from ..collection.model import CollectionModel


class MediaModel(db.Model):
    """
    Represents a media item in the database.
    This model handles metadata, file storage, preview generation, and other media-related operations.
    """

    __private_key = object()
    __versioned__ = {}

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.UnicodeText, nullable=True)
    description = db.Column(db.UnicodeText, nullable=True)
    collectionId = db.Column(db.Integer, db.ForeignKey("collection.id"), nullable=False)
    addedDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)
    ref = db.Column(db.UnicodeText, nullable=True)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)
    CreateDate = db.Column(db.DateTime, nullable=True)
    FileSize = db.Column(db.String, nullable=True)
    ImageHeight = db.Column(db.Integer, nullable=True)
    ImageWidth = db.Column(db.Integer, nullable=True)
    Duration = db.Column(db.String, nullable=True)
    MIMEType = db.Column(db.String, nullable=False)
    dHash = db.Column(db.String, nullable=False)
    md5 = db.Column(db.String, nullable=False, unique=True)

    # remove  uselist=True,?
    task = db.relationship("BackgroundTaskModel", uselist=True, backref="media")

    def __init__(self, metaData: CLMetaData, private_key=None, **kwargs):
        """
        Initialize a MediaModel instance with metadata and optional attributes.

        Args:
            metaData (CLMetaData): Metadata object containing media details.
            private_key: A private key to ensure proper instantiation.
            **kwargs: Additional attributes such as name, collectionLabel, addedDate, etc.

        Raises:
            IncorrectUsageError: If the private key is invalid.
        """
        if private_key != MediaModel.__private_key:
            raise IncorrectUsageError()
        timeNow = datetime.now()

        self.label = kwargs.get("label")
        self.description = kwargs.get("description")
        collection = CollectionModel.create(label=kwargs.get("collectionLabel"))
        self.collectionId = collection.id
        self.addedDate = kwargs.get("addedDate", timeNow)
        self.updatedDate = kwargs.get("updatedDate", self.addedDate)
        self.ref = kwargs.get("ref")
        self.isDeleted = kwargs.get("isDeleted", False)
        self.CreateDate = metaData.CreateDate
        self.FileSize = metaData.FileSize
        self.ImageHeight = metaData.ImageHeight
        self.ImageWidth = metaData.ImageWidth
        self.Duration = metaData.Duration
        self.MIMEType = metaData.MIMEType
        self.dHash = metaData.dHash
        self.md5 = metaData.md5

    def save_to_db(self):
        """Save the current media instance to the database."""
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """Delete the current media instance from the database."""
        db.session.delete(self)
        db.session.commit()

    @property
    def type(self):
        """Determine the media type based on its MIME type."""
        return MediaType.from_mime(self.MIMEType)

    @property
    def extension(self):
        """Guess the file extension based on the MIME type. Defaults to '.bin' if unknown."""
        extension = mimetypes.guess_extension(self.MIMEType)
        if not extension:
            extension = ".bin"
        return extension

    @property
    def filename(self):
        """Generate the relative filename for the media based on its content type and MD5 hash."""
        return os.path.join(self.MIMEType, f"{str(self.md5)}{self.extension}")

    @property
    def preview_filename(self):
        """Generate the filename for the media's preview image."""
        return f"{self.filename}.tn.jpeg"

    @property
    def absolute_filename(self):
        """Get the absolute path to the media file in the storage location."""
        return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.filename)

    @property
    def absolute_preview_filename(self):
        """Get the absolute path to the media's preview image in the storage location."""
        return f"{self.absolute_filename}.tn.jpeg"

    def get_preview(self):
        """
        Retrieve the preview image for the media.
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

    def save(self, metaData: CLMetaData, overwrite=True):
        path = self.absolute_filename
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(metaData.filepath, path)
        self.generate_preview(path, self.absolute_preview_filename)

    @classmethod
    def is_duplicate(
        cls,
        metaData: CLMetaData,
        targetCollectionLabel: int,
    ):
        """
        Check if a media item with the same MD5 hash already exists.
        If it exists in a different collection, raise a DuplicateItemError.
        """
        entity: MediaModel | None = cls.get_by_md5(metaData.md5)
        if entity:
            targetCollection = CollectionModel.find_by_label(targetCollectionLabel)
            currentCollection = CollectionModel.find_by_id(entity.collectionId)
            if currentCollection.id != targetCollection.id:
                raise DuplicateItemError()
        return entity

    @classmethod
    def create(cls, metaData: CLMetaData, **kwargs):
        """
        Create a new media instance.
        If the media is a duplicate, return the existing instance.
        """
        if metaData.md5 is None:
            raise MissingMD5Error()
        if duplicate := cls.is_duplicate(metaData, kwargs.get("collectionLabel")):
            return duplicate
        entity = MediaModel(metaData=metaData, private_key=cls.__private_key, **kwargs)
        entity.save(metaData=metaData)
        entity.save_to_db()
        if entity.type == MediaType.VIDEO:
            hnsw_video_lookup.add(entity.id, entity.dHash)
        elif entity.type == MediaType.IMAGE:
            hnsw_image_lookup.add(entity.id, entity.dHash)
        return entity

    def __eq__(self, other):
        """
        Compare two media instances for equality based on their attributes.
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

    @classmethod
    def update(cls, _id, metaData: CLMetaData | None, **kwargs):
        """
        Update an existing media instance with new metadata or attributes.
        If the updated media is a duplicate, raise a DuplicateItemError.
        """
        currentEntity = cls.get(_id)
        updatedEntity = shutil.copy.deepcopy(currentEntity)
        if metaData:
            if updatedEntity.is_duplicate(metaData, kwargs.get("collectionLabel")):
                raise DuplicateItemError()
            existing_media = updatedEntity.absolute_path()
            updatedEntity.save(metaData=metaData)
            if not existing_media == updatedEntity.absolute_path():
                os.remove(existing_media)
            updatedEntity.CreateDate = metaData.CreateDate
            updatedEntity.FileSize = metaData.FileSize
            updatedEntity.ImageHeight = metaData.ImageHeight
            updatedEntity.ImageWidth = metaData.ImageWidth
            updatedEntity.Duration = metaData.Duration
            updatedEntity.MIMEType = metaData.MIMEType
            updatedEntity.dHash = metaData.dHash
            updatedEntity.md5 = metaData.md5

        updatedEntity.name = kwargs.get("name", updatedEntity.name)
        updatedEntity.ref = kwargs.get("ref", updatedEntity.ref)
        updatedEntity.isDeleted = kwargs.get("isDeleted", updatedEntity.isDeleted)
        if "collectionLabel" in kwargs:
            collection = CollectionModel.create(label=kwargs.get("collectionLabel"))
            updatedEntity.collectionId = collection.id
        if currentEntity != updatedEntity:
            updatedEntity.updatedDate = kwargs.get("updatedDate", datetime.now())
            updatedEntity.save_to_db()
            if metaData:
                if updatedEntity.type == MediaType.VIDEO:
                    hnsw_video_lookup.replace(updatedEntity.id, updatedEntity.dHash)
                elif updatedEntity.type == MediaType.IMAGE:
                    hnsw_image_lookup.replace(updatedEntity.id, updatedEntity.dHash)
            return updatedEntity
        else:
            return currentEntity

    @classmethod
    def get(cls, _id):
        """
        Retrieve a media instance by its ID.
        Raise MissingMediaError if the media does not exist.
        """
        media = cls.query.filter_by(id=_id).first()
        if not media:
            raise MissingMediaError()

        return media

    @classmethod
    def get_all(cls, types=None):
        """
        Retrieve all media instances.
        Optionally filter by media types.
        """
        if not types:
            items = cls.query.all()
        else:
            items = cls.query.filter(MediaModel.type.in_(types)).all()

        return items

    @classmethod
    def get_by_md5(cls, md5):
        """
        Retrieve a media instance by its MD5 hash.
        """
        media = cls.query.filter_by(md5=md5).first()

        return media

    @classmethod
    def delete(cls, _id: int):
        """
        Delete a media instance by its ID.
        Raise HardDeleteFailedError if the media is not marked as deleted.
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
        """Delete all media instances from the database."""
        all = cls.query.all()
        for media in all:
            if not media.isDeleted:
                cls.delete(media.id)

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
                print(f"Timeout waiting for {master_pl}.")
                return False
            time.sleep(1)  # Poll every second
        print("adaptive.m3u8 found!")
        return True

    def get_stream_folder(self):
        """
        Retrieve the folder containing the media's video stream.
        If the stream does not exist, initiate its generation.
        """
        if self.type != "video":  # why MediaType.VIDEO is not working?
            print(f"can't stream {self.id}. not a video")
            raise VideoStreamError(self.id, additionalMessage="not a video")
        stream_path = os.path.join(self.MIMEType, f"media_{str(self.id)}")
        output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
        master_pl = os.path.join(output_dir, "adaptive.m3u8")
        if not os.path.exists(master_pl):
            BackgroundTaskModel.start(self.id, "generate_stream_lq")
            success = self.wait_for_m3u8(master_pl=master_pl)
            if not success:
                raise VideoStreamError(self.id)
        return output_dir


class FileHandler:
    def __init__(self, file):
        pass

    @classmethod
    def save(cls, file):
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)

        # Avoid overwriting by adding a number if file exists
        base, ext = os.path.splitext(temp_path)
        counter = 1
        while os.path.exists(temp_path):
            temp_path = f"{base}_{counter}{ext}"
            counter += 1
        file.save(temp_path)
        return temp_path
