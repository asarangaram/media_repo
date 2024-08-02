from datetime import datetime

from io import BytesIO
import os

from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound


from .hash.image import sha512hash_image
from .hash.video import sha512hash_video
from .hash.md5 import validate_md5String
from ...db import db
from ...config import ConfigClass
from .media_types import MediaType, determine_media_type


class MediaModel(db.Model):
    __private_key = object()

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    type = db.Column(db.UnicodeText, nullable=False)
    collectionLabel = db.Column(db.Integer, nullable=False)
    md5String = db.Column(db.String, nullable=False, unique=True)
    createdDate = db.Column(db.DateTime, nullable=False)
    originalDate = db.Column(db.DateTime, nullable=True)
    updatedDate = db.Column(db.DateTime, nullable=False)
    ref = db.Column(db.UnicodeText, nullable=True)
    isdeleted = db.Column(db.Boolean, default=False, nullable=False)

    path = db.Column(db.UnicodeText, nullable=True)

    def __init__(self, private_key=None, **kwargs):
        timeNow = datetime.now()
        if private_key != MediaModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        self.__bytes_io = kwargs.get("bytes_io")  # This don't go to db
        self.__filename = kwargs.get("filename")
        self.name = kwargs.get("name")
        self.type = kwargs.get("type")
        self.collectionLabel = kwargs.get("collectionLabel")
        self.md5String = kwargs.get("md5String")
        self.createdDate = kwargs.get("createdDate", timeNow)
        self.originalDate = kwargs.get("originalDate")
        self.updatedDate = kwargs.get("updatedDate", timeNow)
        self.ref = kwargs.get("ref")
        self.isdeleted = kwargs.get("isdeleted", False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def absolute_path(self):
        if self.path:
            return os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
        InternalServerError("Media not stored yet")

    def save(self, overwrite=True):
        
        if self.id:
            self.path = os.path.join(f"media_{str(self.id)}", self.__filename)
            path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.__bytes_io.seek(0)
            with open(path, "wb") as file:
                file.write(self.__bytes_io.getvalue())
            del self.__bytes_io
            
        else:
            InternalServerError("Save to DB Failed!!")

    @classmethod
    def find_by_md5String(cls, md5String):
        return cls.query.filter_by(md5String=md5String).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all(cls):
        all = cls.query.all()
        return all

    @classmethod
    def create(cls, **kwargs):
        md5String = kwargs["md5String"]
        bytes_io = kwargs["bytes_io"]
        validate_md5String(bytes_io, md5String)

        has_duplicate = cls.find_by_md5String(md5String)
        if has_duplicate:
            return has_duplicate
        entity = MediaModel(private_key=cls.__private_key, **kwargs)
        entity.save_to_db() # So that we get id!
        entity.save()
        entity.save_to_db()
        return entity

    def replaceMedia(self, filename, bytes_io, md5String):
        if all(arg is None for arg in [filename, bytes_io, md5String]):
            return False
        if any(arg is None for arg in [filename, bytes_io, md5String]):
            if not filename:
                 raise ValidationError( {"filename": ["filename is required to update media"],})
            if not bytes_io:
                 raise ValidationError( {"media": ["media file is not included in the request"],})
            if not md5String:
                 raise ValidationError( {"md5String": ["md5String should be included in the request to update media"],})
             
        validate_md5String(bytes_io, md5String)
        existing_media = self.absolute_path()
        self.__bytes_io = bytes_io
        self.md5String = md5String
        self.__filename = filename
        self.save()
        ##  File saved with different name
        if not existing_media == self.absolute_path():
            os.remove(existing_media)
        return True

    @classmethod
    def update(cls, _id, **kwargs):
        entity = cls.get(_id)

        # if md5String is given, the file is changed.
        # Handle it first!

        isUpdated = entity.replaceMedia(
            bytes_io=kwargs.get("bytes_io"),
            md5String=kwargs.get("md5String"),
            filename=kwargs.get("filename"),
        )
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in ["bytes_io","md5String", "filename" ]}

        for key, value in filtered_kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
                isUpdated = True
        if isUpdated:
            entity.save_to_db()
            return entity
        raise 

    @classmethod
    def get(cls, _id):
        media = cls.find_by_id(_id)
        if not media:
            raise NotFound("media not found")
        return media

    @classmethod
    def get_all(cls):
        return cls.find_all()

    @classmethod
    def delete(cls, _id: int):
        media = cls.get(_id)
        media.delete_from_db()

    @classmethod
    def delete_all(cls):
        all = cls.find_all()
        for media in all:
            media.delete_from_db()
