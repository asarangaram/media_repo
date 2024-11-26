import time
from celery import Celery
from flask import jsonify
from werkzeug.exceptions import InternalServerError, NotFound
from sqlalchemy.schema import UniqueConstraint
from celery.result import AsyncResult
from ...db import db


celery = Celery("tasks", broker="redis://localhost:6379/0", backend='redis://localhost:6379/0')


class BackgroundTaskModel(db.Model):
    __private_key = object()

    __tablename__ = "BackgroundTask"

    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(
        db.Integer, db.ForeignKey("media.id"), nullable=False
    )
    task_name = db.Column(db.String, nullable=False)
    task_id = db.Column(db.Integer, nullable=False)
    task_status = db.Column(db.String)
    __table_args__ = (
        UniqueConstraint('media_id', 'task_name', name='uq_media_task'),
    )

    def __init__(self, media_id, task_name, task_id, private_key=None, **kwargs):
        if private_key != BackgroundTaskModel.__private_key:
            raise InternalServerError("Use Class Method  receive_file.")
        self.media_id = media_id
        self.task_id = task_id
        self.task_name = task_name
        pass

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_default_by_media_id(cls, media_id):
        return cls.query.filter_by(media_id=media_id, task_name='default').first()

    @celery.task(bind=True)
    def default_task(cls, command):
        """Simulate processing of the command"""
        print(f"Processing: {command}")
        time.sleep(10)  # Simulate a long-running task
        print(f"Finished: {command}")
        return f"Task {command} completed"

    @classmethod
    def start_task(cls, media_id):
        result = cls.default_task.apply_async(args=[media_id])
        obj = BackgroundTaskModel(
            media_id=media_id,
            task_name = 'default',
            task_id=result.id,
            private_key=BackgroundTaskModel.__private_key,
        )
        obj.save_to_db()
        obj.update_status()

        return obj

    def restart_task(self, media_id):
        result = self.default_task.apply_async(args=[media_id])
        
        self.task_name = 'default';
        self.task_id=result.id
        self.save_to_db()
        self.update_status()

    def update_status(self):
        task_id = self.task_id
        try:
            task_result =  self.default_task.AsyncResult(task_id)
            print(f"state is {task_result.state}")
            if task_result.state == "PENDING":
                self.task_status = "pending"
            elif task_result.state == "SUCCESS":
                self.task_status = "completed"
            elif task_result.state == "REVOKED":
                self.task_status = "cancelled"
            else:
                self.task_status = "inprogress"
        except:
            self.task_status = "notfound"
        self.save_to_db()


    @classmethod
    def get(cls, media_id):
        obj = cls.find_default_by_media_id(media_id=media_id)
        if  obj:
            obj.update_status()
            return obj
        raise NotFound(f"task with  media id {media_id} not found")
     

    @classmethod
    def start(cls, media_id):
        obj = cls.find_default_by_media_id(media_id=media_id)
        if not obj:
            obj = cls.start_task(media_id)
        else:
            obj.restart_task(media_id)
        
        return obj

    
