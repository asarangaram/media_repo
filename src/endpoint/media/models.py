from datetime import datetime

from io import BytesIO
import mimetypes
import os
import shutil


from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound


from ..collection.model import CollectionModel

from .hash.md5 import get_md5_hexdigest
from ...db import db
from ...config import ConfigClass
from ...utils.image_thumbnail import create_image_thumbnail
from ...utils.video_thumbnail import create_video_thumbnail
from .media_types import MediaType, determine_media_type, determine_mime


class MediaModel(db.Model):
    __private_key = object()

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    type = db.Column(db.UnicodeText, nullable=False)
    content_type = db.Column(db.String, nullable=False)
    collectionLabel = db.Column(
        db.String, db.ForeignKey("collection.label"), nullable=False
    )
    md5String = db.Column(db.String, nullable=False, unique=True)
    createdDate = db.Column(db.DateTime, nullable=False)
    originalDate = db.Column(db.DateTime, nullable=True)
    updatedDate = db.Column(db.DateTime, nullable=False)
    ref = db.Column(db.UnicodeText, nullable=True)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

    path = db.Column(db.UnicodeText, nullable=True)

    def __init__(self, private_key=None, **kwargs):
        timeNow = datetime.now()
        if private_key != MediaModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        self.__bytes_io = kwargs.get("bytes_io")  # This don't go to db
        self.__filename = kwargs.get("filename")
        self.name = kwargs.get("name", self.__filename) 

        self.collectionLabel = kwargs.get("collectionLabel")
        self.md5String = kwargs.get("md5String")
        self.createdDate = kwargs.get("createdDate", timeNow)
        self.originalDate = kwargs.get("originalDate")
        self.updatedDate = kwargs.get("updatedDate", self.createdDate)
        self.ref = kwargs.get("ref")
        self.isDeleted = kwargs.get("isDeleted", False)
        self.content_type = determine_mime(self.__bytes_io, kwargs.get("content_type"))
        self.fExt = mimetypes.guess_extension(self.content_type)
        self.type = determine_media_type(self.__bytes_io, self.content_type)
        CollectionModel.create(self.collectionLabel)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def absolute_path(self):
        if self.path:
            return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
        raise InternalServerError("Media not stored yet")

    

    def preview_path(self):
        if self.path:
            preview = os.path.join(
                ConfigClass.FILE_STORAGE_LOCATION, f"{self.path}.tn.jpg"
            )
            path = self.absolute_path()
            if not os.path.exists(preview):
                self.generate_preview(path, preview)
            return preview
        raise InternalServerError("Media not stored yet")

    def generate_preview(self, path, preview):
        try:
            if self.type == MediaType.VIDEO:
                create_video_thumbnail(path, preview)
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
            if has_duplicate.collectionLabel != kwargs["collectionLabel"]:
                raise ValidationError(
                    {
                        "collectionLabel": [
                            f"duplicate item found in {has_duplicate.collectionLabel}, with id {has_duplicate.id}"
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
            raise InternalServerError(f"The media you are trying to replace is already present with id {searchResult.id}")
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
        filtered_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in ["bytes_io", "filename"]
        }

        for key, value in filtered_kwargs.items():
            if hasattr(entity, key):
                if not getattr(entity, key) == value:
                    setattr(entity, key, value)
                    isUpdated = True
        if isUpdated:
            if not filtered_kwargs.get('updatedDate'):
                entity.updatedDate  = datetime.now()
            entity.save_to_db()
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
        media =  cls.query.filter_by(md5String=md5String).first()
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
