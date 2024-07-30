from io import BytesIO
from werkzeug.datastructures import FileStorage


def load_image_from_werkzeug_cache(im: FileStorage):
    """ If successful, return the bytes, else raise exceptions"""
    bytes_io = BytesIO()
    im.save(bytes_io)
    if bytes_io.getbuffer().nbytes == 0:
        raise Exception("Empty File")

    bytes_io.seek(0)
    return bytes_io
