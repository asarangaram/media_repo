# --- 1. _Constants.py ---
import cv2


class Configs:
    OUTPUT_DIR = "generated_media"
    MIME_TYPES = {
        "image/jpeg": {"extension": "jpg",  "fourcc": None},
        "image/png": {"extension": "png",  "fourcc": None},
        "image/tiff": {"extension": "tif",  "fourcc": None},
        "image/gif": {
            "extension": "gif",
            
            "fourcc": None,
        },  # Note: OpenCV saves static GIF
        "image/webp": {"extension": "webp",  "fourcc": None},
        "video/mp4": {
            "extension": "mp4",
            
            "fourcc": cv2.VideoWriter_fourcc(*"mp4v"),
        },  # H.264/MPEG-4 AVC
        "video/mov": {
            "extension": "mov",
            
            "fourcc": cv2.VideoWriter_fourcc(*"mp4v"),
        },  # Often same as MP4
        "video/x-msvideo": {
            "extension": "avi",
            
            "fourcc": cv2.VideoWriter_fourcc(*"MJPG"),
        },  # Motion JPEG for AVI
        "video/x-matroska": {
            "extension": "mkv",
            
            "fourcc": cv2.VideoWriter_fourcc(*"H264"),
        },  # H.264 for MKV
        # OpenCV: FFMPEG: tag 0x30385056/'VP80' is not supported with codec id 139 and format 'webm / WebM'
        #"video/webm": {
        #    "extension": "webm",
        #    
        #    "fourcc": cv2.VideoWriter_fourcc(*"VP80"),
        #},  # VP8 for WebM
    }