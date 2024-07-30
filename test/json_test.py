import json
import sqlalchemy as db

# Create a SQLite database in memory (you can use a different database URL)
database_url = 'sqlite:///:memory:'
isFlask = False
if not isFlask:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    Base = declarative_base()


class ImageModelException(Exception):
    pass


class EXIFModel(Base):
    __private_key = object()

    __tablename__ = "exif_data"

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, nullable=False, unique=True)
    ISO = db.Column(db.Integer)
    Flash = db.Column(db.Integer)
    ColorSpace = db.Column(db.Integer)
    Compression = db.Column(db.Integer)
    LightSource = db.Column(db.Integer)
    Orientation = db.Column(db.Integer)
    XResolution = db.Column(db.Integer)
    YResolution = db.Column(db.Integer)
    ExposureMode = db.Column(db.Integer)
    MeteringMode = db.Column(db.Integer)
    WhiteBalance = db.Column(db.Integer)
    ExifImageWidth = db.Column(db.Integer)
    ResolutionUnit = db.Column(db.Integer)
    ExifImageHeight = db.Column(db.Integer)
    DigitalZoomRatio = db.Column(db.Integer)
    SceneCaptureType = db.Column(db.Integer)
    YCbCrPositioning = db.Column(db.Integer)
    ExposureCompensation = db.Column(db.Integer)
    Make = db.Column(db.UnicodeText)
    Model = db.Column(db.UnicodeText)
    Software = db.Column(db.UnicodeText)
    CreateDate = db.Column(db.UnicodeText)
    ExifVersion = db.Column(db.UnicodeText)
    FlashpixVersion = db.Column(db.UnicodeText)
    DateTimeOriginal = db.Column(db.UnicodeText)
    ComponentsConfiguration = db.Column(db.UnicodeText)
    FNumber = db.Column(db.Double)
    ExposureTime = db.Column(db.Double)
    ApertureValue = db.Column(db.Double)
    ShutterSpeedValue = db.Column(db.Double)

    def __init__(self, image_id, data, private_key=None):
        if private_key != EXIFModel.__private_key:
            raise ImageModelException("Use Class Method  fromJSON.")
        self.image_id = image_id
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ', '.join([f"{key}={value}" for key, value in self.__dict__.items()])
        return f"EXIFModel({attributes})"

    @classmethod
    def fromJSON(cls, image_id, json_data):
        data = json.loads(json_data)

        exif = EXIFModel(image_id, data, private_key=cls.__private_key)
        exif.save_to_db()
        # exif.print()
        return exif

    def save_to_db(self):
        if isFlask:
            db.session.add(self)
            db.session.commit()
        else:
            session = Session()
            session.add(self)
            session.commit()
            session.close()

    def delete_from_db(self):
        if isFlask:
            db.session.delete(self)
            db.session.commit()
        else:
            session = Session()
            session.add(self)
            session.commit()
            session.close()

    @classmethod
    def find_all(cls):
        if isFlask:
            all = cls.query.all()
        else:
            session = Session()
            all = session.query(EXIFModel).all()
            session.close()
        return all


if __name__ == '__main__':
    json_exif = """{
        "ISO": 640,
        "Make": "Microsoft",
        "Flash": 16,
        "Model": "Lumia 532 Dual SIM",
        "FNumber": 2.4,
        "Software": "Windows Phone",
        "ColorSpace": 1,
        "CreateDate": "2015:07:22 12:09:28",
        "Compression": 6,
        "ExifVersion": "0220",
        "LightSource": 0,
        "Orientation": 1,
        "XResolution": 72,
        "YResolution": 72,
        "ExposureMode": 0,
        "ExposureTime": 0.02,
        "MeteringMode": 1,
        "WhiteBalance": 0,
        "ApertureValue": 2.39999932487398,
        "ExifImageWidth": 1456,
        "ResolutionUnit": 2,
        "ExifImageHeight": 2592,
        "FlashpixVersion": "0100",
        "DateTimeOriginal": "2015:07:22 12:09:28",
        "DigitalZoomRatio": 1,
        "SceneCaptureType": 0,
        "YCbCrPositioning": 1,
        "ShutterSpeedValue": 0.0200000026308365,
        "ExposureCompensation": 0,
        "ComponentsConfiguration": "1 2 3 0",
        "Unwanted:": "Unwanted Value"
    }"""
    json_exif2 = """{
        "ISO": 640,
        "Make": "Microsoft"

    }"""
    json_exif3 = """{
        "ISO": 640,
        "Make": "Microsoft",
        "Flash": 16,
        "Model": "Lumia 532 Dual SIM",
        "FNumber": 2.4,
        "Software": "Windows Phone",
        "ColorSpace": 1,
        "Compression": 6,
        "ExifVersion": "0220",
        "LightSource": 0,
        "Orientation": 1,
        "XResolution": 72,
        "YResolution": 72,
        "ExposureMode": 0,
        "ExposureTime": 0.02,
        "MeteringMode": 1,
        "WhiteBalance": 0,
        "ApertureValue": 2.39999932487398,
        "ExifImageWidth": 1456,
        "ResolutionUnit": 2,
        "ExifImageHeight": 2592,
        "FlashpixVersion": "0100",
        "DateTimeOriginal": "2015:07:22 12:09:28",
        "DigitalZoomRatio": 1,
        "SceneCaptureType": 0,
        "YCbCrPositioning": 1,
        "ShutterSpeedValue": 0.0200000026308365,
        "ExposureCompensation": 0,
        "ComponentsConfiguration": "1 2 3 0"
    }"""
    if not isFlask:
        Base.metadata.create_all(engine)

    exif = EXIFModel.fromJSON(0, json_exif)
    exif = EXIFModel.fromJSON(2, json_exif2)
    exif = EXIFModel.fromJSON(4, json_exif3)

    items = EXIFModel.find_all()
    for item in items:
        print(item.CreateDate)
