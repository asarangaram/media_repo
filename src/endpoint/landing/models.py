
from src.config import ConfigClass

_info = """
This API service offers microservices through a RESTful interface. \
Please refer to the appropriate endpoint that aligns with your specific needs. \
Consult the API documentation or relevant resources to identify the correct endpoints for the functionalities you require.
""".strip()


class LandingPageModel:
    def __init__(self):
        self.name = ConfigClass.APP_NAME
        self.info = _info
        self.id = 100  # TODO: FIND A UNIQUE ID FOR EACH SERVER AND REPLACE


""" class ServerStatusModel(db.Model):
    __private_key = object()

    __tablename__ = "server_status"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False, unique=True)
    updatedDate = db.Column(db.DateTime, nullable=False)

    def __init__(
        self,
        tableName,
        private_key=None,
    ):
        if private_key != ServerStatusModel.__private_key:
            raise InternalServerError("Use Class Method  create / update.")
        self.name = tableName

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def to_json(self):
        return {self.name: int(toTimeStamp(self.updatedDate))}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_all(cls):
        all = cls.query.all()
        return all

    @classmethod
    def update_time_stamp(cls, tableName):
        entity = cls.find_by_name(tableName)
        if not entity:
            entity = ServerStatusModel(
                tableName,
                private_key=cls.__private_key,
            )
        entity.updatedDate = datetime.now()
        entity.save_to_db()
 """
