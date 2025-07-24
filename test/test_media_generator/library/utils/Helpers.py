from typing import List, Optional, Tuple
import cv2
import numpy as np


import os
import random
import subprocess
from datetime import datetime

from .TimeStamp import fromTimeStamp
from .errors import JSONValidationError

class Helpers:
    @staticmethod
    def create_base_frame(
        width: int, height: int, background_color: tuple = None
    ) -> np.ndarray:
        """Creates a blank frame with a specified or random background color."""
        if background_color is None:
            background_color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        return np.full((height, width, 3), background_color, dtype=np.uint8)

    
    

    @staticmethod
    def rgb_to_bgr(color_rgb: list[int]) -> tuple[int, int, int]:
        """Converts an RGB color list to a BGR tuple for OpenCV. Clamps values to 0-255."""
        if color_rgb is None:
            return None
        r, g, b = (
            max(0, min(255, color_rgb[0])),
            max(0, min(255, color_rgb[1])),
            max(0, min(255, color_rgb[2])),
        )
        return (b, g, r)

    @staticmethod
    def draw_text_with_outline(
        frame: np.ndarray,
        text: str,
        position: tuple[int, int],  # Bottom-left corner of the text
        font: int,
        font_scale: float,
        font_thickness: int,
        text_color_bgr: tuple[int, int, int],
        outline_color_bgr: tuple[int, int, int] = (0, 0, 0),  # Default to black outline
        outline_thickness_factor: float = 2.0,
    ):
        """Draws text on a frame with an outline for better readability."""
        outline_thickness = int(font_thickness * outline_thickness_factor)

        # Draw outline
        cv2.putText(
            frame,
            text,
            position,
            font,
            font_scale,
            outline_color_bgr,
            outline_thickness,
            cv2.LINE_AA,
        )

        # Draw actual text
        cv2.putText(
            frame,
            text,
            position,
            font,
            font_scale,
            text_color_bgr,
            font_thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def apply_metadata(
        filepath: str,
        media_type: str,
        creation_date: datetime,
        comments: list[str] = None,
    ):
        """Applies creation date and comments using ExifTool."""
        if not os.path.exists(filepath):
            print(f"Error: File not found for metadata application: {filepath}")
            return

        # ExifTool prefers YYYY:MM:DD HH:MM:SS format for many tags
        date_str_exif = creation_date.strftime("%Y:%m:%d %H:%M:%S")

        exiftool_command = ["exiftool"]

        # Common date tags for images and videos
        if "image" in media_type:
            exiftool_command.extend(
                [
                    f"-DateTimeOriginal={date_str_exif}",  # For photos
                    f"-CreateDate={date_str_exif}",  # General image creation date
                    f"-ModifyDate={date_str_exif}",  # Modification date
                    f"-FileCreateDate={date_str_exif}",  # File system creation date
                    f"-FileModifyDate={date_str_exif}",  # File system modification date
                ]
            )
        elif "video" in media_type:
            exiftool_command.extend(
                [
                    f"-QuickTime:CreateDate={date_str_exif}",
                    f"-QuickTime:ModifyDate={date_str_exif}",
                    f"-QuickTime:TrackCreateDate={date_str_exif}",
                    f"-QuickTime:TrackModifyDate={date_str_exif}",
                    f"-QuickTime:MediaCreateDate={date_str_exif}",
                    f"-QuickTime:MediaModifyDate={date_str_exif}",
                    f"-Keys:CreationDate={date_str_exif}",  # Newer MP4 (ISO BMFF) tag
                    f"-FileCreateDate={date_str_exif}",
                    f"-FileModifyDate={date_str_exif}",
                ]
            )

        # Embed comments (using various tags for broader compatibility)
        if comments:
            for comment in comments:
                exiftool_command.extend(
                    [
                        f"-UserComment={comment}",  # EXIF UserComment
                        f"-Comment={comment}",  # EXIF Comment
                        f"-XMP-dc:Description={comment}",  # XMP Description
                        f"-EXIF:ImageDescription={comment}",  # EXIF ImageDescription (for images)
                    ]
                )
                if "video" in media_type:
                    exiftool_command.append(
                        f"-QuickTime:Comment={comment}"
                    )  # QuickTime specific comment

        exiftool_command.extend(
            [
                "-overwrite_original",  # Overwrite the original file (the temp one)
                "-q",  # Quiet output
                "-m",  # Ignore minor warnings
                filepath,
            ]
        )

        print(f"Applying metadata to {filepath}...")
        try:
            result = subprocess.run(
                exiftool_command, capture_output=True, text=True, check=True
            )
            if "files updated" in result.stderr:
                print("Metadata successfully updated by ExifTool.")
            else:
                print(
                    f"ExifTool operation might not have succeeded as expected. Output:\n{result.stderr}"
                )
        except subprocess.CalledProcessError as e:
            print(f"Error calling ExifTool: {e}")
            print(f"ExifTool stdout:\n{e.stdout}")
            print(f"ExifTool stderr:\n{e.stderr}")
        except FileNotFoundError:
            print(
                "Error: ExifTool not found. Please ensure it's installed and in your PATH."
            )
    @staticmethod
    def _convert_color_tuple(
        color_list: Optional[List[int]],
    ) -> Optional[Tuple[int, int, int]]:
        if color_list is None:
            return None
        if (
            isinstance(color_list, list)
            and len(color_list) == 3
            and all(isinstance(c, int) for c in color_list)
        ):
            return tuple(color_list)
        elif (
            isinstance(color_list, tuple)
            and len(color_list) == 3
            and all(isinstance(c, int) for c in color_list)
        ):
            return color_list

        raise JSONValidationError("Invalid Color [r, g, b]")

    @staticmethod
    def _convert_position_tuple(
        pos_list: Optional[List[int]],
    ) -> Optional[Tuple[int, int]]:
        if (
            isinstance(pos_list, list)
            and len(pos_list) == 2
            and all(isinstance(p, int) for p in pos_list)
        ):
            return tuple(pos_list)
        if pos_list is None:
            return None
        raise JSONValidationError("Invalid Position [x,y]")

    @staticmethod
    def _convert_ms_to_datetime(ms_since_epoch: Optional[int]) -> Optional[datetime]:
        if ms_since_epoch is None:
            return None
        return fromTimeStamp(ms_since_epoch)
