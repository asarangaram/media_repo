from io import BytesIO
from werkzeug.datastructures import FileStorage
from PIL import Image

from io import BytesIO



class ImageLoaderError(Exception):
    pass

def load_media_from_werkzeug_cache(im: FileStorage):
    """ If successful, return the bytes, else raise exceptions"""
    try:
        bytes_io = BytesIO()
        im.save(bytes_io)

        # confirm the file is not empty
        if bytes_io.getbuffer().nbytes == 0:
            raise Exception("Empty File")
        # Confirm image
        bytes_io.seek(0)    
        with Image.open(bytes_io) as img:
            img.verify()
        bytes_io.seek(0)

        return bytes_io
    except Exception as e:
        err =ImageLoaderError( f"File is  not a image")
        raise err
    


