from datetime import datetime
from werkzeug.exceptions import UnsupportedMediaType, InternalServerError, NotFound

from src.endpoint.landing.models import ServerStatusModel

from ...db import db


class CollectionModel(db.Model):
    __private_key = object()

    __tablename__ = "collection"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.UnicodeText, nullable=False, unique=True)
    description = db.Column(db.UnicodeText, nullable=True)
    createdDate = db.Column(db.DateTime, nullable=False)
    updatedDate = db.Column(db.DateTime, nullable=False)   
    isDeleted = db.Column(db.Boolean, default=False, nullable=False)
    media = db.relationship("MediaModel", uselist=True, backref="collection")

    def __init__( self, private_key=None, **kwargs ):
        if private_key != CollectionModel.__private_key:
            raise InternalServerError("Use Class Method  create / update.")
        timeNow = datetime.now()
        self.label = kwargs.get("label")
        self.description = kwargs.get("description")
        self.createdDate = kwargs.get("createdDate", timeNow)
        self.updatedDate = kwargs.get("updatedDate", self.createdDate)
        self.isDeleted = kwargs.get("isDeleted", False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        ServerStatusModel.update_time_stamp(self.__tablename__)

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        ServerStatusModel.update_time_stamp(self.__tablename__)

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
    def create( cls,   **kwargs):
        """ 
        If the label is present, we return the existing one, else
        create one. Note, we can't provide description here.
        """
        time_now = datetime.now()
        entity = cls.find_by_label(label=kwargs.get("label"))
        if entity:
            # update values? debate
            return entity 
        entity = CollectionModel(private_key=cls.__private_key,**kwargs )
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
    
    @classmethod
    def update(cls, id, **kwargs):
        time_now = datetime.now()
        entity:CollectionModel|None = cls.find_by_id(id=id)
        if not entity:
            raise NotFound(f"Entity with id {id} not found")
        entity.label = kwargs.get("label",  entity.label)
        entity.description = kwargs.get("description", entity.description)
        entity.createdDate = kwargs.get("createdDate", entity.createdDate)
        entity.updatedDate = kwargs.get("updatedDate", entity.updatedDate)
        entity.isDeleted = kwargs.get("isDeleted", entity.isDeleted )
        entity.save_to_db()
        return entity
    
    @classmethod
    def delete(cls, id):
        entity:CollectionModel|None = cls.find_by_id(id=id)
        if not entity:
            raise NotFound(f"Entity with id {id} not found")
        if entity.media:
            raise InternalServerError(f"Can't delete actively used collection. Remove media before deleting the collection")
        entity.delete_from_db()
                
        
