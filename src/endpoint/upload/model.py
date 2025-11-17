import hashlib
import shutil
from pathlib import Path
from typing import Any

from src.config import ConfigClass
from src.endpoint.entity.temp_file import TempFile


class UploadManager:
    def __init__(self, session_id: str, uploaded_file: Any) -> None:
        self.session_id = session_id
        self.uploaded_file = uploaded_file

    @classmethod
    def remove(cls, file_path: Path) -> None:
        if file_path.exists():
            file_path.unlink()

    def upload_files(self):
        session_path = (
            Path(ConfigClass.UPLOAD_STORAGE_LOCATION) / self.session_id
        )
        session_path.mkdir(parents=True, exist_ok=True)

        temp_file = TempFile(self.uploaded_file)
        metadata = temp_file.metadata()
        # metadata = {key: value for key, value in metadata.items() if value}

        md5 = metadata.get("md5")
        if not md5:
            hash_md5 = hashlib.md5()
            with open(temp_file.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                md5 = hash_md5.hexdigest()

        _, ext = self.uploaded_file.filename.split(".", 1)
        unique_name = md5 + "." + ext

        file_path = session_path / unique_name

        result = {"file_identifier": unique_name, **metadata}

        if file_path.exists():
            result["status"] = "duplicate"
        else:
            shutil.move(temp_file.path, file_path)
            result["status"] = "success"
        if temp_file:
            temp_file.remove()
        return result
