from ...db import db

from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from datetime import datetime


class Item(db.Model):
    __versioned__ = {}
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.UnicodeText, nullable=True)  # Nullable for Medias
    description = db.Column(db.UnicodeText)
    isCollection = db.Column(db.Boolean)
    parentId = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False if not isCollection else True,
    )
    createdDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)

    type = db.Column(db.String(50))
    __mapper_args__ = {"polymorphic_on": type}
    __table_args__ = (
        db.UniqueConstraint("label", "isCollection", name="unique_label_Collection"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def create(self, media_info_data=None):
        if self.isCollection:
            raise ValueError("Media must have isCollection set to False")
        if self.parentId is None:
            raise ValueError("Media must have a parentId")

        self.createdDate = datetime.now()
        self.updatedDate = self.createdDate

        db.session.add(self)
        db.session.commit()
        db.session.flush()

        if media_info_data:
            media_info_data["id"] = self.id  # Ensure correct linkage
            media_info = MediaInfo(**media_info_data)
            db.session.add(media_info)
            db.session.commit()

        return self

    def update(self, **kwargs):
        updated = False
        mediaInfo = MediaInfo.get(self.id)
        if mediaInfo:
            (_, updated) = mediaInfo.update(**kwargs)

        for key, value in kwargs.items():
            if key in ["label", "description", "isDeleted", "parentId"]:
                if getattr(self, key) != value:
                    setattr(self, key, value)
                    updated = True

        if updated:
            self.updatedDate = datetime.now()
            db.session.commit()

        return (self, updated)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return jsonify({"message": "Deleted successfully"})

    @classmethod
    def get(cls, id):
        item = cls.query.get(id)
        return jsonify(item.to_dict()) if item else jsonify({"error": "Not found"}), 404


class MediaInfo(db.Model):
    __versioned__ = {}
    __tablename__ = "media_info"
    id = db.Column(db.Integer, db.ForeignKey("items.id"), primary_key=True)
    date = db.Column(db.DateTime, nullable=True)

    size = db.Column(db.Integer, nullable=False)
    md5 = db.Column(db.String, nullable=False)
    dHash = db.Column(db.String, nullable=False)
    mimeType = db.Column(db.String, nullable=False)

    height = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Integer, nullable=True)

    Media = db.relationship("Media", back_populates="MediaInfo")

    def __init__(self, **kwargs):
        _ = {key: kwargs[key] for key in kwargs if key in self.__table__.columns}
        super().__init__(**_)

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def update(self, **kwargs):
        updated = False
        for key, value in kwargs.items():
            if key in self.__table__.columns and key != "id":
                if getattr(self, key) != value:
                    setattr(self, key, value)
                    updated = True

        if updated:
            db.session.commit()

        return (self, updated)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return jsonify({"message": "Deleted successfully"})

    @classmethod
    def get(cls, id):
        media_info = cls.query.get(id)
        return (
            jsonify(media_info.to_dict())
            if media_info
            else jsonify({"error": "Not found"})
        ), 404


class Collection(Item):
    __mapper_args__ = {"polymorphic_identity": "collection"}


class Media(Item):
    __mapper_args__ = {"polymorphic_identity": "media"}
    MediaInfo = db.relationship("MediaInfo", uselist=False, back_populates="Media")
