import time
from celery import Celery
from flask import jsonify
from werkzeug.exceptions import InternalServerError, NotFound
from sqlalchemy.schema import UniqueConstraint
from celery.result import AsyncResult

from src.celery import CeleryTasks


from ...db import db


class BackgroundTaskModel(db.Model):
    __private_key = object()

    __tablename__ = "BackgroundTask"

    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey("entities.id"), nullable=False)
    task_name = db.Column(db.String, nullable=False)
    task_id = db.Column(db.Integer, nullable=False)
    task_status = db.Column(db.String)
    __table_args__ = (UniqueConstraint("media_id", "task_name", name="uq_media_task"),)

    def __init__(self, media_id, task_name, private_key=None, **kwargs):
        if private_key != BackgroundTaskModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        self.media_id = media_id
        self.task_name = task_name
        pass

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def update_status(self):
        task_id = self.task_id
        try:
            task_result = CeleryTasks.exec_generate_preview.AsyncResult(task_id)
            print(f"state is {task_result.state}")
            if task_result.state == "PENDING":
                self.task_status = "pending"
            elif task_result.state == "SUCCESS":
                self.task_status = "completed"
            elif task_result.state == "REVOKED":
                self.task_status = "cancelled"
            elif task_result.state == "FAILURE":
                self.task_status = "failed"
            else:
                self.task_status = "inprogress"
        except:
            self.task_status = "notfound"
        self.save_to_db()

    @classmethod
    def get_status(cls, media_id, task_name):
        obj = cls.query.filter_by(media_id=media_id, task_name=task_name).first()
        if obj:
            obj.update_status()
            return obj
        raise NotFound(f"task with  media id {media_id} not found")

    def start_task(self):
        if self.task_name == "generate_stream_lq":
            result = CeleryTasks.exec_generate_stream_lq.apply_async(
                args=[
                    self.media_id,
                ]
            )
        else:
            raise InternalServerError(
                f"{self.task_name} is not a valid background task"
            )

        self.task_id = result.id
        self.save_to_db()
        self.update_status()
        return self

    @classmethod
    def start(cls, media_id, task_name):
        obj = cls.query.filter_by(media_id=media_id, task_name=task_name).first()
        if not obj:
            obj = BackgroundTaskModel(
                media_id=media_id,
                task_name=task_name,
                private_key=BackgroundTaskModel.__private_key,
            )
        return obj.start_task()

    @classmethod
    def start_all(cls, media_id):
        return [
            cls.start(media_id, task_name=taskname) for taskname in CeleryTasks.tasks
        ]

    @classmethod
    def get_all(cls, media_id):
        return [
            cls.get_status(media_id, task_name=taskname)
            for taskname in CeleryTasks.tasks
        ]
