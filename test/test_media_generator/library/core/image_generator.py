from dataclasses import dataclass
import os
from typing import Optional, Tuple

import cv2



from ..utils.Helpers import Helpers
from ..utils.configs import Configs
from ..utils.errors import JSONValidationError
from .base_media import BaseMedia

@dataclass
class FrameDescription:
    background_color: Optional[Tuple[int, int, int]] = None  # BGR
    num_shapes: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict):
        processed_data = data.copy()
        if "background_color" in processed_data:
            processed_data["background_color"] = (
                Helpers._convert_color_tuple(
                    processed_data.get("background_color")
                )
            )
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in processed_data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """Converts the FrameDescription instance to a dictionary for JSON serialization."""
        return self.__dict__.copy()

@dataclass
class ImageGenerator(BaseMedia):
    frame: Optional[FrameDescription] = None
   

    @classmethod
    def from_dict(cls, data: dict):
        # Process base fields first, get them as a dictionary
        base_fields_dict = BaseMedia.from_dict(data).__dict__

        # Process frame field
        if "frame" in data and isinstance(data["frame"], dict):
            frame_instance = FrameDescription.from_dict(data["frame"])
        elif "frame" not in data:
            raise JSONValidationError("ImageDescription missing 'frame' data.")
        else:
            raise JSONValidationError("Invalid 'frame' data for ImageDescription.")

        # Construct a dictionary with all arguments for ImageDescription's __init__
        # This ensures correct argument passing order for the dataclass constructor.
        init_args = {
            **base_fields_dict,  # All fields from BaseMedia
            "frame": frame_instance,  # Specific field for ImageDescription
        }

        # Filter to ensure only valid fields for ImageDescription are passed
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_init_args = {k: v for k, v in init_args.items() if k in valid_keys}

        return cls(**filtered_init_args)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["frame"] = self.frame.to_dict()
        return data
    
    def generate(self):
        frame = Helpers.create_base_frame(
            self.width, self.height, self.frame.background_color
        )
        if self.frame.num_shapes and self.frame.num_shapes > 0:
            for _ in range(self.frame.num_shapes):
                Helpers.draw_random_shape(frame)
        

        filepath = os.path.join(Configs.OUTPUT_DIR, self.fileName)
        directory, _ = os.path.split(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

        cv2.imwrite(filepath, frame)

        print(f"Image '{self.fileName} {os.path.abspath(filepath)}' created by OpenCV.")

