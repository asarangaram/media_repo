import os
import json

import cv2
from sqlalchemy import Column, Integer, JSON, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
"""
It is intentional that create_all() is not called
"""


class FaceDB(Base):
    __tablename__ = "faces"

    create_table_query = """
        CREATE TABLE IF NOT EXISTS faces (
            id INT AUTO_INCREMENT PRIMARY KEY,
            json_data JSON
        )
    """
    id = Column(Integer, primary_key=True)
    json_data = Column(JSON)

    def __init__(self, session, image):
        self.id = image["id"]
        self.session = session
        r = self.load(self.session, self.id)
        if r:
            self.json = json.loads(r.json_data)
            self.is_new = False
        else:
            self.json = image
            self.is_new = True

    def update(self, key, value):
        self.json[key] = value
        pass

    def save(self):
        self.json_data = json.dumps(self.json)
        if self.is_new:
            self.session.add(self)
        self.session.commit()

    @classmethod
    def load(cls, session, user_id):
        return session.query(cls).get(user_id)

    @classmethod
    def create_table(cls, session):
        session.execute(text(cls.create_table_query))
