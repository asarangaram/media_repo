from datetime import datetime

import mimetypes
import os
import shutil
import time

from clmediakit import (
    create_image_thumbnail,
    create_video_thumbnail4x4,
    MediaType,
    CLMetaData,
)

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
    __private_key = object()
    __versioned__ = {}

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    collectionId = db.Column(db.Integer, db.ForeignKey("collection.id"), nullable=False)
    createdDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)
    ref = db.Column(db.UnicodeText, nullable=True)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

    # remove  uselist=True,?
    task = db.relationship("BackgroundTaskModel", uselist=True, backref="media")

    def __init__(self, metaData: CLMetaData, private_key=None, **kwargs):
        if private_key != MediaModel.__private_key:
            raise IncorrectUsageError()
        timeNow = datetime.now()

        self.name = kwargs.get("name", self.__filename)
        collection = CollectionModel.create(label=kwargs.get("collectionLabel"))
        self.collectionId = collection.id
        self.createdDate = kwargs.get("createdDate", timeNow)
        self.updatedDate = kwargs.get("updatedDate", self.createdDate)
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
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @property
    def type(self):
        return MediaType.from_mime(self.MIMEType)

    @property
    def extension(self):
        extension = mimetypes.guess_extension(self.MIMEType)
        if not extension:
            extension = ".bin"
        return extension

    @property
    def filename(self):
        return os.path.join(self.content_type, f"{str(self.md5)}{self.extension}")

    @property
    def preview_filename(self):
        return f"{self.filename}.tn.jpeg"

    @property
    def absolute_filename(self):
        return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.filename)

    @property
    def absolute_preview_filename(self):
        return f"{self.absolute_filename}.tn.jpeg"

    def get_preview(self):
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
        entity: MediaModel | None = cls.get_by_md5String(metaData.md5)
        if entity:
            targetCollection = CollectionModel.find_by_label(targetCollectionLabel)
            currentCollection = CollectionModel.find_by_id(entity.collectionId)
            if currentCollection.id != targetCollection.id:
                raise DuplicateItemError()
        return entity

    @classmethod
    def create(cls, metaData: CLMetaData, **kwargs):
        if metaData.md5 is None:
            raise MissingMD5Error()
        if duplicate := cls.is_duplicate(metaData, kwargs.get("collectionLabel")):
            return duplicate
        entity = MediaModel(metaData=metaData, private_key=cls.__private_key, **kwargs)
        entity.save(metaData=metaData)
        entity.save_to_db()
        return entity

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.id == other.id
            and self.name == other.name
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
            updatedEntity.updatedDate = datetime.now()
            updatedEntity.save_to_db()
            return updatedEntity
        else:
            return currentEntity

    @classmethod
    def get(cls, _id):
        media = cls.query.filter_by(id=_id).first()
        if not media:
            raise MissingMediaError()
        media.fExt = mimetypes.guess_extension(media.content_type)
        return media

    @classmethod
    def get_all(cls, types=None):
        if not types:
            items = cls.query.all()
        else:
            items = cls.query.filter(MediaModel.type.in_(types)).all()
        for item in items:
            item.fExt = mimetypes.guess_extension(item.content_type)
        return items

    @classmethod
    def get_by_md5String(cls, md5String):
        media = cls.query.filter_by(md5String=md5String).first()
        if media:
            media.fExt = mimetypes.guess_extension(media.content_type)
        return media

    @classmethod
    def delete(cls, _id: int):
        entity = cls.get(_id)
        if not entity.isDeleted:
            raise HardDeleteFailedError()

        path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, entity.path)
        if os.path.exists(path):
            os.remove(path)
        entity.delete_from_db()

    @classmethod
    def delete_all(cls):
        all = cls.query.all()
        for media in all:
            media.delete_from_db()

    @classmethod
    def wait_for_m3u8(self, master_pl: str, timeout: int = 60):
        """Wait for adaptive.m3u8 file to be written within the timeout."""
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
        if self.type != "video":  # why MediaType.VIDEO is not working?
            print(f"can't stream {self.id}. not a video")
            raise VideoStreamError(self.id, additionalMessage="not a video")
        stream_path = os.path.join(self.content_type, f"media_{str(self.id)}")
        output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
        master_pl = os.path.join(output_dir, "adaptive.m3u8")
        if not os.path.exists(master_pl):
            BackgroundTaskModel.start(self.id, "generate_stream_lq")
            success = self.wait_for_m3u8(master_pl=master_pl)
            if not success:
                raise VideoStreamError(self.id)
        return output_dir
