from datetime import datetime

import mimetypes
import os
import shutil
from threading import Thread
import time

from marshmallow import ValidationError
from werkzeug.exceptions import InternalServerError, NotFound

from src.celery import CeleryTasks
from src.endpoint.background.models import BackgroundTaskModel

from ...endpoint.background.wrapper import startBackgroundProcess
from ...endpoint.landing.models import ServerStatusModel
from ...media_processing.hls_streaming.hls_stream_generator import (
    HLSStreamGenerator,
    HLSVariant,
)

from ..collection.model import CollectionModel

from .hash.md5 import get_md5_hexdigest
from ...db import db
from ...config import ConfigClass
from ...media_processing.create_thumbnails.image_thumbnail import create_image_thumbnail
from ...media_processing.create_thumbnails.video_thumbnail import (
    create_video_thumbnail4x4,
)
from .media_types import MediaType, determine_media_type, determine_mime


class MediaModel(db.Model):
    __private_key = object()
    __versioned__ = {}

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    type = db.Column(db.UnicodeText, nullable=False)
    content_type = db.Column(db.String, nullable=False)
    collectionId = db.Column(db.Integer, db.ForeignKey("collection.id"), nullable=False)
    md5String = db.Column(db.String, nullable=False, unique=True)
    createdDate = db.Column(db.DateTime, nullable=False)
    originalDate = db.Column(db.DateTime, nullable=True)
    updatedDate = db.Column(db.DateTime, nullable=False)
    ref = db.Column(db.UnicodeText, nullable=True)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

    path = db.Column(db.UnicodeText, nullable=True)
    # remove  uselist=True,?
    task = db.relationship("BackgroundTaskModel", uselist=True, backref="media")

    def __init__(self, private_key=None, **kwargs):
        if private_key != MediaModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        timeNow = datetime.now()
        self.__bytes_io = kwargs.get("bytes_io")  # This don't go to db
        self.__filename = kwargs.get("filename")
        self.name = kwargs.get("name", self.__filename)

        collection = CollectionModel.create(label=kwargs.get("collectionLabel"))
        self.collectionId = collection.id
        self.md5String = kwargs.get("md5String")
        self.createdDate = kwargs.get("createdDate", timeNow)
        self.originalDate = kwargs.get("originalDate")
        self.updatedDate = kwargs.get("updatedDate", self.createdDate)
        self.ref = kwargs.get("ref")
        self.isDeleted = kwargs.get("isDeleted", False)
        self.content_type = determine_mime(self.__bytes_io, kwargs.get("content_type"))
        self.fExt = mimetypes.guess_extension(self.content_type)
        self.type = determine_media_type(self.__bytes_io, self.content_type)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        ServerStatusModel.update_time_stamp(self.__tablename__)

    def delete_from_db(self):
        db.session.delete(self)

        db.session.commit()
        ServerStatusModel.update_time_stamp(self.__tablename__)

    def absolute_path(self):
        if self.path:
            abs_path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
            if not os.path.exists(abs_path):
                raise InternalServerError("Media file not found")
            return abs_path
        raise InternalServerError("Media not stored yet")

    def preview_absolute_path_name(self):
        return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, f"{self.path}.tn.jpg")

    def preview_path(self):
        if self.path:
            path = self.absolute_path()
            preview = self.preview_absolute_path_name()
            path = self.absolute_path()
            if not os.path.exists(preview):
                self.generate_preview(path, preview)
            if os.path.exists(preview):
                return preview
            else:
                raise NotFound("failed to generate preview")
        raise InternalServerError("Media not stored yet")

    def generate_preview(self, path, preview):
        try:
            if self.type == MediaType.VIDEO:
                create_video_thumbnail4x4(path, preview)
            if self.type == MediaType.IMAGE:
                create_image_thumbnail(path, preview)
            return
        except Exception as e:
            raise InternalServerError(f"failed to generate preview {e}")

    def save(self, overwrite=True):
        if self.id:
            if not self.fExt:
                self.fExt = mimetypes.guess_extension(self.content_type)
            self.path = os.path.join(
                self.content_type, f"media_{str(self.id)}{self.fExt}"
            )
            path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.__bytes_io.seek(0)
            with open(path, "wb") as file:
                file.write(self.__bytes_io.getvalue())
            del self.__bytes_io
            preview = self.preview_absolute_path_name()
            self.generate_preview(path, preview)
        else:
            raise InternalServerError("Media not in DB")

    @classmethod
    def create(cls, **kwargs):
        bytes_io = kwargs["bytes_io"]
        md5String = get_md5_hexdigest(
            bytes_io,
        )

        has_duplicate: MediaModel | None = cls.get_by_md5String(md5String)
        if has_duplicate:
            targetCollection = CollectionModel.find_by_label(
                kwargs.get("collectionLabel")
            )
            currentCollection = CollectionModel.find_by_id(has_duplicate.collectionId)
            if currentCollection.id != targetCollection.id:
                raise ValidationError(
                    {
                        "collectionLabel": [
                            f"duplicate item found in {currentCollection.label}, with id {has_duplicate.id}"
                        ],
                    }
                )
            return has_duplicate
        entity = MediaModel(
            private_key=cls.__private_key, md5String=md5String, **kwargs
        )
        entity.save_to_db()  # So that we get id!
        entity.save()
        entity.save_to_db()
        startBackgroundProcess(entity.id)

        return entity

    def replaceMedia(self, filename, bytes_io):
        if all(arg is None for arg in [filename, bytes_io]):
            return False
        if any(arg is None for arg in [filename, bytes_io]):
            if not filename:
                raise ValidationError(
                    {
                        "filename": ["filename is required to update media"],
                    }
                )
            if not bytes_io:
                raise ValidationError(
                    {
                        "media": ["media file is not included in the request"],
                    }
                )

        existing_media = self.absolute_path()
        self.__bytes_io = bytes_io
        md5String = get_md5_hexdigest(
            bytes_io,
        )
        # What if the replacement provide is already present
        # in the DB with different id?
        searchResult = self.get_by_md5String(md5String)
        if searchResult:
            raise InternalServerError(
                f"The media you are trying to replace is already present with id {searchResult.id}"
            )
        self.md5String = md5String
        self.__filename = filename
        self.save()
        # File saved with different name
        if not existing_media == self.absolute_path():
            os.remove(existing_media)
        return True

    @classmethod
    def update(cls, _id, **kwargs):
        entity = cls.get(_id)
        isUpdated = entity.replaceMedia(
            bytes_io=kwargs.get("bytes_io"),
            filename=kwargs.get("filename"),
        )
        fileChanged = isUpdated
        filtered_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in ["bytes_io", "filename"]
        }
        print(f"before: entity.collectionId = {entity.collectionId}")
        if "collectionLabel" in kwargs:
            collection = CollectionModel.create(label=kwargs.get("collectionLabel"))
            entity.collectionId = collection.id
        print(f"after: entity.collectionId = {entity.collectionId}")

        for key, value in filtered_kwargs.items():
            if hasattr(entity, key):
                if not getattr(entity, key) == value:
                    setattr(entity, key, value)
                    isUpdated = True
        if isUpdated:
            if not filtered_kwargs.get("updatedDate"):
                entity.updatedDate = datetime.now()
            entity.save_to_db()
            if fileChanged:
                startBackgroundProcess(id=entity.id)

        return entity

    @classmethod
    def get(cls, _id):
        media = cls.query.filter_by(id=_id).first()
        if not media:
            raise NotFound("media not found")
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
        media = cls.get(_id)
        if not media.isDeleted:
            raise ValidationError(
                {
                    "isDeleted": [
                        "only soft deleted media can be permanently deleted."
                    ],
                }
            )

        path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, media.path)
        if os.path.exists(path):
            os.remove(path)
        media.delete_from_db()

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
            raise InternalServerError(f"can't stream {self.id}. not a video")
        stream_path = os.path.join(self.content_type, f"media_{str(self.id)}")
        output_dir = os.path.join(ConfigClass.STREAM_STORAGE_LOCATION, stream_path)
        master_pl = os.path.join(output_dir, "adaptive.m3u8")
        if not os.path.exists(master_pl):
            BackgroundTaskModel.start(self.id, "generate_stream_lq")
            success = self.wait_for_m3u8(master_pl=master_pl)
            if not success:
                raise InternalServerError(f"failed to get stream for {self.id}")
        return output_dir
