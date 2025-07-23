

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ..utils.TimeStamp import toTimeStamp
from ..utils.Helpers import Helpers

@dataclass
class BaseMedia:
    MIMEType: str
    width: int
    height: int
    fileName: Optional[str] = None
    label: Optional[str] = None
    CreateDate: Optional[int] = None
    comments: List[str] = field(default_factory=list)

    

    @classmethod
    def from_dict(cls, data: dict):
        processed_data = data.copy()
        if "CreateDate" in processed_data and processed_data["CreateDate"] is not None:
            processed_data["CreateDate"] = Helpers._convert_ms_to_datetime(
                processed_data["CreateDate"]
            )
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in processed_data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """Converts the BaseMediaDescription instance to a dictionary for JSON serialization."""
        data = self.__dict__.copy()
        # Convert datetime object back to milliseconds since epoch if it was converted
        if isinstance(data.get("CreateDate"), datetime):
            data["CreateDate"] = toTimeStamp(data["CreateDate"])
        return data

    def generate(self):
        raise Exception("Implement in subclass")
    
