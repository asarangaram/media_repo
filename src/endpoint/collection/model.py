from datetime import datetime
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound

from ...db import db


class CollectionModel(db.Model):
    __private_key = object()

    __tablename__ = "collection"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.UnicodeText, nullable=False, unique=True)
    description = db.Column(db.UnicodeText, nullable=True)
    createdDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)

    def __init__(
        self,
        label: str,
        description: str,
        createdDate: datetime,
        updatedDate: datetime,
        private_key=None,
    ):
        if private_key != CollectionModel.__private_key:
            raise InternalServerError("Use Class Method  create / update.")
        self.label = label
        self.description = description
        self.createdDate = createdDate
        self.updatedDate = updatedDate

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
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all(cls):
        all = cls.query.all()
        return all

    @classmethod
    def create( cls, label: str):
        """ 
        If the label is present, we return the existing one, else
        create one. Note, we can't provide description here.
        """
        time_now = datetime.now()
        entity = cls.find_by_label(label=label)
        if entity:
            return entity 
        entity = CollectionModel(
            label=label,
            description=None,
            createdDate= time_now ,
            updatedDate=time_now,
            private_key=cls.__private_key,
        )
        entity.save_to_db()
        return entity
    
    @classmethod
    def get(cls, _id):
        entity = cls.find_by_id(_id)
        if not entity:
            raise Exception(f"Entity with id {_id} not found")
        return entity
    
    @classmethod
    def get_all(cls):
        return cls.find_all()
    
    @classmethod
    def update(cls, _id, _label=None, _description=None):
        time_now = datetime.now()
        entity:CollectionModel|None = cls.find_by_id(_id=_id)
        if not entity:
            raise Exception(f"Entity with id {_id} not found")
        if _label :
            entity.label = _label 
        if _description:
            entity.description = _description
        if _label or _description:
            entity.updatedDate = time_now
            entity.save_to_db()
        return entity
    
    @classmethod
    def delete(cls, _id):
        entity:CollectionModel|None = cls.find_by_id(_id=_id)
        if not entity:
            raise Exception(f"Entity with id {_id} not found")
        entity.delete_from_db()
                
        
