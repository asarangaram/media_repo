from datetime import datetime
import shutil
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound


from ...db import db


class CollectionModel(db.Model):
    __private_key = object()
    __versioned__ = {}

    __tablename__ = "collection"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.UnicodeText, nullable=False, unique=True)
    description = db.Column(db.UnicodeText, nullable=True)
    addedDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)
    media = db.relationship("MediaModel", uselist=True, backref="collection")

    def __init__(self, private_key=None, **kwargs):
        if private_key != CollectionModel.__private_key:
            raise InternalServerError("Use Class Method  create / update.")
        timeNow = datetime.now()
        self.label = kwargs.get("label")
        self.description = kwargs.get("description")
        self.addedDate = kwargs.get("addedDate", timeNow)
        self.updatedDate = kwargs.get("updatedDate", self.addedDate)
        self.isDeleted = kwargs.get("isDeleted", False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_label(cls, label):
        return cls.query.filter_by(label=label).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_all(cls):
        all = cls.query.all()
        return all

    @classmethod
    def create(cls, **kwargs):
        """
        If the label is present, we return the existing one, else
        create one. Note, we can't provide description here.
        """
        time_now = datetime.now()
        entity = cls.find_by_label(label=kwargs.get("label"))
        if entity:
            # update values? debate
            return entity
        entity = CollectionModel(private_key=cls.__private_key, **kwargs)
        entity.save_to_db()
        return entity

    @classmethod
    def get(cls, id):
        entity = cls.find_by_id(id)
        if not entity:
            raise NotFound(f"Entity with id {id} not found")
        return entity

    @classmethod
    def get_all(cls):
        return cls.find_all()

    def __eq__(self, other):
        """
        Compare two collection instances for equality based on their attributes.
        """
        if not isinstance(other, self.__class__):
            return False

        return (
            self.label == other.label
            and self.description == other.description
            and self.isDeleted == other.isDeleted
        )

    @classmethod
    def update(cls, id, **kwargs):
        currentEntity: CollectionModel | None = cls.find_by_id(id=id)
        if not currentEntity:
            raise NotFound(f"Entity with id {id} not found")
        updatedEntity = shutil.copy.deepcopy(currentEntity)
        updatedEntity.label = kwargs.get("label", updatedEntity.label)
        updatedEntity.description = kwargs.get("description", updatedEntity.description)
        updatedEntity.isDeleted = kwargs.get("isDeleted", updatedEntity.isDeleted)
        if currentEntity != updatedEntity:
            updatedEntity.updatedDate = kwargs.get("updatedDate", datetime.now())
            updatedEntity.save_to_db()
            return updatedEntity
        else:
            return updatedEntity

    @classmethod
    def delete(cls, id):
        entity: CollectionModel | None = cls.find_by_id(id=id)
        if not entity:
            raise NotFound(f"Entity with id {id} not found")
        if entity.media:
            raise InternalServerError(
                f"Can't delete actively used collection. Remove media before deleting the collection"
            )
        entity.delete_from_db()
