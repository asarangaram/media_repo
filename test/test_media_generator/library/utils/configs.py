# --- 1. _Constants.py ---
import cv2


class Configs:
    OUTPUT_DIR = "generated_media"
    MIME_TYPES = {
        "image/jpeg": {"extension": "jpg", "is_image": True, "fourcc": None},
        "image/png": {"extension": "png", "is_image": True, "fourcc": None},
        "image/tiff": {"extension": "tif", "is_image": True, "fourcc": None},
        "image/gif": {
            "extension": "gif",
            "is_image": True,
            "fourcc": None,
        },  # Note: OpenCV saves static GIF
        "image/webp": {"extension": "webp", "is_image": True, "fourcc": None},
        "video/mp4": {
            "extension": "mp4",
            "is_image": False,
            "fourcc": cv2.VideoWriter_fourcc(*"mp4v"),
        },  # H.264/MPEG-4 AVC
        "video/mov": {
            "extension": "mov",
            "is_image": False,
            "fourcc": cv2.VideoWriter_fourcc(*"mp4v"),
        },  # Often same as MP4
        "video/x-msvideo": {
            "extension": "avi",
            "is_image": False,
            "fourcc": cv2.VideoWriter_fourcc(*"MJPG"),
        },  # Motion JPEG for AVI
        "video/x-matroska": {
            "extension": "mkv",
            "is_image": False,
            "fourcc": cv2.VideoWriter_fourcc(*"H264"),
        },  # H.264 for MKV
        "video/webm": {
            "extension": "webm",
            "is_image": False,
            "fourcc": cv2.VideoWriter_fourcc(*"VP80"),
        },  # VP8 for WebM
    }