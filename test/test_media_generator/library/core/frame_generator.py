from dataclasses import dataclass, field
import random
from typing import List, Optional, Tuple

from ..utils.Helpers import Helpers
from .basic_shapes import Shape, Shapes

@dataclass
class FrameGenerator:
    background_color: Optional[Tuple[int, int, int]] = None  # BGR
    num_shapes: Optional[int] = None
    shapes: Optional[int] = None
    shapes: List[Shape] = field(default_factory=list)

    
    def with_shapes(self):
        if self.num_shapes and self.num_shapes > 0:
            self.shapes = [
                Shapes[random.choice(["circle", "rectangle", "line", "triangle"])].from_dict(
                    {"thickness":random.randint(-1, 3),
                    "color":(
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    )},
                )
                for _ in range(self.num_shapes)
            ]
        else:
            self.shapes = []
        return self

    @classmethod
    def from_dict(cls, data: dict):
        processed_data = data.copy()
        if "background_color" in processed_data:
            processed_data["background_color"] = Helpers._convert_color_tuple(
                processed_data.get("background_color")
            )
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in processed_data.items() if k in valid_keys}
        frameGenerator = cls(**filtered_data).with_shapes()
        return frameGenerator

    def to_dict(self) -> dict:
        """Converts the FrameDescription instance to a dictionary for JSON serialization."""
        return self.__dict__.copy()

    

    def generate(self, width: int, height: int):
        frame = Helpers.create_base_frame(width, height, self.background_color)
        if self.shapes:
            for shape in self.shapes:
                shape.draw(frame)

        return frame
