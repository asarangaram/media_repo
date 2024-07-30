import json
import os
import shutil
import base64

from werkzeug.datastructures import FileStorage
from datetime import datetime

from .metadata import EXIFModel

from ...db import db
from ...config import ConfigClass
from ...image_proc import hash
from ...image_proc.file_utilities import load_image_from_werkzeug_cache as image_loader

from ...image_proc.image_tools import ImageTools


class ImageModelException(Exception):
    pass


class ImageModel(db.Model):
    __private_key = object()

    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    path = db.Column(db.UnicodeText, nullable=True)
    datetime = db.Column(db.DateTime, nullable=False)
    sha512hash = db.Column(db.String(128), nullable=False, unique=True)
    create_on_the_fly = True
    force_load_from_image = True

    exif = db.relationship("EXIFModel", uselist=False, backref="images")

    def __init__(self, image, sha512hash, private_key=None):
        if private_key != ImageModel.__private_key:
            raise ImageModelException("Use Class Method  receive_file.")
        self.name = image.filename
        self.datetime = datetime.now()
        self.sha512hash = sha512hash

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_basepath(cls):
        return ConfigClass.FILE_STORAGE_LOCATION

    @classmethod
    def get_absolutepath(cls, relPath):
        if not relPath:
            return None
        return os.path.join(cls.get_basepath(), relPath)

    def absolute_path(self):
        return self.get_absolutepath(self.path)
    
    def set_path(self):
        self.path = os.path.join(f"image_{str(self.id)}", self.name)
        self.save_to_db()
        return

    def save_image(self, bytes_io, overwrite=True):
        if self.absolute_path():
            os.makedirs(self.absolute_path(), exist_ok=True)
            with open(self.absolute_path(), "wb") as file:
                file.write(bytes_io.getvalue())
            self.save_to_db()
            return

    def jsonify(self, has_thumbnail=False):
        result = {
            "id": self.id,
            "uploadtime": self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return result

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
    def create(cls, image: FileStorage):
        entity = None
        try:
            image_data = image_loader(image)
            sha512hash = hash.sha512hash(image_data=image_data)

            has_duplicate = cls.find_by_sha512hash(sha512hash)
            if has_duplicate:
                return has_duplicate, None

            entity = ImageModel(
                image=image, sha512hash=sha512hash, private_key=cls.__private_key
            )

            if entity:
                entity.save_to_db()
                entity.set_path()
                entity.save_image(image_data)
                EXIFModel.read_from_image(entity)

                return entity, None
            raise ImageModelException("Failed to upload")
        except Exception as e:
            return entity, str(e)

    @classmethod
    def get(cls, _id):
        try:
            image = cls.find_by_id(_id)
            if image:
                return image, None
            raise ImageModelException("image not found")

        except Exception as e:
            return None, str(e)

    @classmethod
    def groupByDate(cls, all):
        result = {}
        for image in all:
            tag = "not dated"
            exif = image.exif
            if exif and exif.year and exif.month and exif.day:
                tag = f"{exif.year} {exif.month} {exif.day}"
            if tag not in result:
                result[tag] = []
            result[tag].append(image.jsonify(has_thumbnail=True))

        return result

    @classmethod
    def get_all(cls):
        try:
            all = cls.find_all()
            result = {}
            if all:
                result = cls.groupByDate(all)
            return result, None
        except Exception as e:
            return None, str(e)

    @classmethod
    def delete(cls, _id: int):
        try:
            image = cls.find_by_id(_id)

            if image:
                print(f"PATH IS {image.path}")
                shutil.rmtree(os.path.dirname(image.path))
                image.delete_from_db()
                return None
            raise ImageModelException("image is not found; Not deleted")
        except Exception as e:
            return str(e)

    @classmethod
    def delete_all(cls):
        try:
            all = cls.find_all()
            if all:
                result = {}
                for image in all:
                    err = cls.delete(_id=image.id)
                    if err:
                        result[image.id] = err
                if result:
                    ImageModelException(
                        "not all images are deleted"
                    )
                return {"success": "all images deleted"}, None
            raise ImageModelException("No image found")
        except Exception as e:
            return None, str(e)

    def get_thumbnail_path(self):
        try:
            thumbnail = os.path.join(
                ConfigClass.FILE_STORAGE_LOCATION, f"image_{str(self.id)}", "thumbnail.png"
            )

            if not os.path.isfile(thumbnail):
                with ImageTools(self.absolute_path()) as image_tools:
                    image_tools.create_thumbnail(thumbnail)

            if os.path.isfile(thumbnail):
                return thumbnail, None
            raise ImageModelException("Unable to create thumbnail")

        except Exception as e:
            return None, str(e)
