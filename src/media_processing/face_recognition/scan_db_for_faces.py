import os
import sys
import cv2
import json
import time
from loguru import logger

from src.config import ConfigClass

from src.image_proc.face_recognition.db_access.image import ImageDB, DBase
from src.image_proc.face_recognition.db_access.faces import FaceDB
from src.image_proc.face_recognition.detect_face_facenet_pytorch import detect_faces

logger.remove(0)
logger.add("performance.log", format="{time} | {level} | {message}", level="INFO")
logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO")


def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        logger.info(
            f"{func.__name__} Execution time: {execution_time:.2f} ms, {result}"
        )
        return result

    return wrapper


class FaceScanner(FaceDB):
    def detect_faces(self, method: str, detect_faces_fn, retry=False):
        if method not in self.json or retry:
            img = cv2.imread(self.json["path"])
            if img is not None:
                try:
                    faces = detect_faces_fn(img, prob_low=0.9)
                except BaseException:
                    print(f'{self.json["id"]} failed')

                self.update(method, faces)

                self.save_faces(
                    method,
                    img,
                )
            else:
                logger.critical(
                    f'Error: decode failed, image id {self.json["id"]}, path:{self.json["path"]}'
                )
        return self

    def save_faces(self, method, img):
        for i, face in enumerate(self.json[method]):
            x0, y0, x1, y1 = face["pos"]
            face_cropped = img[y0:y1, x0:x1]
            cv2.imwrite(self.get_path(i, method), face_cropped)
        return self

    def get_path(self, i, method):
        path = os.path.dirname(self.json["path"])
        output_path = os.path.join(path, f"face_{str(i).zfill(4)}.png")
        output_path = output_path.replace("image_repo", f"image_repo_faces_by_{method}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return output_path


@measure_time
def scan_db_for_faces(
    start=0,
    count=1000,
    db_uri=ConfigClass.SQLALCHEMY_DATABASE_URI,
):
    images = ImageDB(db_uri).get_images(limit=count, offset=start)
    with DBase(db_uri) as db:
        FaceScanner.create_table(db.session)
        for image in images:
            FaceScanner(db.session, image).detect_faces(
                "facenet_pytorch", detect_faces, retry=True
            ).save()
    return f"start={start}, count={count}"


if __name__ == "__main__":
    batch_size = 100

    for i in range(578):
        try:
            scan_db_for_faces(start=i * batch_size, count=batch_size)
        except BaseException:
            logger.critical(f"Error: Batch {i} failed")
