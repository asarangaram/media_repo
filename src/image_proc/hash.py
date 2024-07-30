from PIL import Image, ImageFile
import hashlib
from pillow_heif import register_heif_opener
# TODO: Do we need to record if the image is truncated?
ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()

def sha512hash(image_data):
    with Image.open(image_data) as im:
        hash = hashlib.sha512(im.tobytes()).hexdigest()
    return hash
