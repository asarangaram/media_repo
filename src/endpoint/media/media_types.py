from enum import StrEnum
from io import BytesIO
import magic
import re
from marshmallow import fields, ValidationError

class MediaType(StrEnum):
  TEXT='text'
  IMAGE='image'
  VIDEO='video'
  URL='url'
  AUDIO='audio'
  FILE='file'

def contains_url(text):
    if '\n'  in text or '\r'  in text:
        return False

    stripped_text = text.strip()
    
    url_pattern = re.compile(
        r'^http[s]?:\/\/(?:[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=]|%[0-9a-fA-F][0-9a-fA-F])+$'
    )
    return bool(url_pattern.match(stripped_text))

def determine_mime(bytes_io:BytesIO,  file_type:str|None) -> MediaType:
    if not file_type:
        bytes_io.seek(0)         
        # Create a Magic object
        mime = magic.Magic(mime=True)
    
        # Determine the file type
        file_type = mime.from_buffer(bytes_io.getvalue())
        if not file_type :
            file_type = 'application/octet-stream'
    return file_type


def determine_media_type(bytes_io:BytesIO,  file_type:str) -> MediaType:
    if file_type.startswith('image'):
        return MediaType.IMAGE
    elif file_type.startswith('video'):
        return MediaType.VIDEO
    elif file_type.startswith('audio'):
        return MediaType.AUDIO
    elif  file_type.startswith('text'):
        text = bytes_io.getvalue().decode('utf-8')
        if contains_url(text):
            return MediaType.URL
        else:
            return MediaType.TEXT
    else:
        return MediaType.FILE
    

class MediaTypeField(fields.Str):
    def __init__(self, *args, **kwargs):
        self.enum = kwargs.pop('enum', None)
        super().__init__(*args, **kwargs)

    def _validate(self, value):
        if self.enum and value not in self.enum.__members__:
            raise ValidationError(f"Invalid value. Expected one of: {list(self.enum.__members__)}")

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        self._validate(value)
        return value
