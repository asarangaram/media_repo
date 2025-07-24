import cv2

# OpenCV: FFMPEG: tag 0x30385056/'VP80' is not supported with codec id 139 and format 'webm / WebM'
# "video/webm": {
#    "extension": "webm",
#
#    "fourcc": cv2.VideoWriter_fourcc(*"VP80"),
# },  # VP8 for WebM


class Configs:
    OUTPUT_DIR = "generated_media"
    
    FOURCC = {
        "video/mp4": cv2.VideoWriter_fourcc(*"mp4v"),
        "video/mov": cv2.VideoWriter_fourcc(*"mp4v"),
        "video/x-msvideo": cv2.VideoWriter_fourcc(*"MJPG"),
        "video/x-matroska": cv2.VideoWriter_fourcc(*"H264"),
    }
    MIME_TYPES = {
        "image/jpeg": {"extension": "jpg"},
        "image/png": {"extension": "png"},
        "image/tiff": {"extension": "tif"},
        "image/gif": {"extension": "gif"},
        "image/webp": {"extension": "webp"},
        "video/mp4": {"extension": "mp4"},
        "video/mov": {"extension": "mov"},
        "video/x-msvideo": {"extension": "avi"},
        "video/x-matroska": {"extension": "mkv"},
    }
