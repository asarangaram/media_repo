import json
import sys
import random
import datetime
from typing import List, Dict, Any, Tuple

from library.utils.errors import JSONValidationError
from library.utils.TimeStamp import toTimeStamp
from library.media_generator import MediaGenerator

PossibleEnhancements = """
# 
1. Add Text Object and include text.
2. Fix the position of the text
3. Investigate why exiftool fails for few formats
4. Add more Metadata, location, face id, etc
5. Embed properties in the file name.

"""
MIN_WIDTH = 640
MAX_WIDTH = 3840
MIN_HEIGHT = 480
MAX_HEIGHT = 2160

MIN_DATE = datetime.datetime(2020, 1, 1, 0, 0, 0)
MAX_DATE = datetime.datetime(2024, 12, 31, 23, 59, 59)

COMMON_COMMENTS = [
    "A great shot!",
    "Needs editing.",
    "Good quality.",
    "Blurry.",
    "For internal review.",
    "Customer facing.",
    "Draft version.",
    "Final cut.",
    "Placeholder content.",
    "To be updated.",
]

MIN_COMMENTS_PER_ITEM = 1
MAX_COMMENTS_PER_ITEM = 3

MIN_SHAPES = 3
MAX_SHAPES = 10

MIN_SCENE_DURATION = 2
MAX_SCENE_DURATION = 8
MIN_SCENES_PER_VIDEO = 2
MAX_SCENES_PER_VIDEO = 5

FPS_OPTIONS = [24, 25, 30, 60]

# --- Helper Functions for Random Values ---


def random_color_tuple() -> Tuple[int, int, int]:
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def random_date_in_range(
    min_dt: datetime.datetime, max_dt: datetime.datetime
) -> datetime.datetime:
    time_diff = max_dt - min_dt
    random_seconds = random.uniform(0, time_diff.total_seconds())
    return min_dt + datetime.timedelta(seconds=random_seconds)


def random_comments_list() -> List[str]:
    num_comments = random.randint(MIN_COMMENTS_PER_ITEM, MAX_COMMENTS_PER_ITEM)
    return random.sample(COMMON_COMMENTS, k=min(num_comments, len(COMMON_COMMENTS)))


def generate_single_frame_description() -> Dict[str, Any]:
    frame_data: Dict[str, Any] = {}
    frame_data["background_color"] = random_color_tuple()
    frame_data["num_shapes"] = random.randint(MIN_SHAPES, MAX_SHAPES)
    frame_data["include_info"] = True  # random.choice([True, False])
    return frame_data


def generate_single_scene_description() -> Dict[str, Any]:
    """Generates a random SceneDescription dictionary."""
    scene_data = generate_single_frame_description()  # Inherit frame properties
    scene_data["duration"] = random.randint(MIN_SCENE_DURATION, MAX_SCENE_DURATION)
    return scene_data


def generate_single_media_descriptor(media_type: str, index: int) -> Dict[str, Any]:
    available_mime_types = [
        mime_type
        for mime_type in MediaGenerator.supportedMIME()
        if mime_type.startswith(f"{media_type}/")
    ]

    if not available_mime_types:
        return {}

    mime_type = random.choice(available_mime_types)

    descriptor: Dict[str, Any] = {
        "fileName": f"{media_type}_{index:04d}",
        "label": f"Random {mime_type.split('/')[0].capitalize()} {index:04d}",
        "MIMEType": mime_type,
        "width": random.randint(MIN_WIDTH, MAX_WIDTH),
        "height": random.randint(MIN_HEIGHT, MAX_HEIGHT),
        "CreateDate": toTimeStamp(random_date_in_range(MIN_DATE, MAX_DATE)),
        "comments": random_comments_list(),
    }

    if mime_type.startswith("image/"):
        # Image-specific fields
        descriptor["frame"] = generate_single_frame_description()

    elif mime_type.startswith("video/"):
        # Video-specific fields
        descriptor["fps"] = random.choice(FPS_OPTIONS)
        num_scenes = random.randint(MIN_SCENES_PER_VIDEO, MAX_SCENES_PER_VIDEO)
        descriptor["scenes"] = [
            generate_single_scene_description() for _ in range(num_scenes)
        ]

    if not descriptor["comments"]:
        del descriptor["comments"]

    return descriptor


def generate_media_list_dict(
    image_count: int, video_count: int
) -> Dict[str, List[Dict[str, Any]]]:
    media_list = []
    if image_count > 0:
        media_list.extend(
            [generate_single_media_descriptor("image", index) for index in range(image_count)]
        )
    if video_count > 0:
        media_list.extend(
            [generate_single_media_descriptor("video", index) for index in range(video_count)]
        )
    return {"media_list": media_list}


if __name__ == "__main__":
    random.seed(42)
    try:
        data = generate_media_list_dict(image_count=300, video_count=50)
        print("Generated Sample JSON Data:")
        # print(json.dumps(data, indent=2))
        with open("sampleconfig.json", "w") as f:
            f.write(json.dumps(data, indent=2))
        mediaGenerator =MediaGenerator.from_dict(outdir='generated_media',data=data,  )
        mediaGenerator.generate()
    except json.JSONDecodeError:
        print("Error decoding JSON ")
        sys.exit(1)

    except JSONValidationError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
