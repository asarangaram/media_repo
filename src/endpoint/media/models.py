from datetime import datetime

from io import BytesIO
import os

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound



from .hash.image import sha512hash_image
from .hash.video import sha512hash_video
from ...db import db
from ...config import ConfigClass
from .media_types import MediaType, determine_media_type


class MediaModel(db.Model):
    __private_key = object()

    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    type = db.Column(db.UnicodeText, nullable=False)
    path = db.Column(db.UnicodeText, nullable=True)
    created_time = db.Column(db.DateTime, nullable=False)
    sha512hash = db.Column(db.String(128), nullable=False, unique=True)

    def __init__(
        self,
        name: str,
        bytes_io: BytesIO,
        type: MediaType,
        created_time: datetime,
        sha512hash: str,
        process_time: float,
        private_key=None,
    ):
        if private_key != MediaModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        self.name = name
        self.type = type
        self.created_time = created_time
        self.sha512hash = sha512hash
        self.__bytes_io = bytes_io  # This don't go to db
        self.process_time = process_time

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
        self.save_to_db()
        if self.id:
            self.path = os.path.join(f"image_{str(self.id)}", self.name)
            path = os.path.join(ConfigClass.FILE_STORAGE_LOCATION, self.path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.__bytes_io.seek(0)
            with open(path, "wb") as file:
                file.write(self.__bytes_io.getvalue())
            self.__bytes_io = None  # free buffer
            self.save_to_db()
        else:
            InternalServerError("Save to DB Failed!!")

    @classmethod
    def find_by_sha512hash(cls, sha512hash):
        return cls.query.filter_by(sha512hash=sha512hash).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all(cls):
        all = cls.query.all()
        return all

    @classmethod
    def load(cls, mediaCache: FileStorage):
        if mediaCache.filename == "":
            raise UnsupportedMediaType("Media name is not specified")
        time_now = datetime.now()
        bytes_io = BytesIO()
        mediaCache.save(bytes_io)

        # confirm the file is not empty
        if bytes_io.getbuffer().nbytes == 0:
            raise UnsupportedMediaType("Empty File")

        type = determine_media_type(bytes_io)
        bytes_io.seek(0)
        entity = None

        match (type):
            case MediaType.IMAGE:
                hash_hex, process_time = sha512hash_image(image_stream=bytes_io)

            case MediaType.VIDEO:
                hash_hex, process_time = sha512hash_video(video_stream=bytes_io)

            # TODO: add support for  MediaType.AUDIO | MediaType.TEXT
            case _:
                raise UnsupportedMediaType(f"Unsupported Media Content")

        return MediaModel(
            name=mediaCache.filename,
            bytes_io=bytes_io,
            type=type,
            created_time=time_now,
            sha512hash=hash_hex,
            process_time=process_time,
            private_key=cls.__private_key,
        )

    @classmethod
    def create(cls, mediaCache: FileStorage):
        entity = cls.load(mediaCache)
        has_duplicate = cls.find_by_sha512hash(entity.sha512hash)
        if has_duplicate:
            return has_duplicate
        entity.save()
        return entity

    @classmethod
    def get(cls, _id):
        image = cls.find_by_id(_id)
        if not image:
            raise NotFound("image not found")
        return image

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
        for image in all:
            image.delete_from_db()
