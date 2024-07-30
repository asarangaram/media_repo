from enum import StrEnum
import magic
import re

class MediaType(StrEnum):
  TEXT='text'
  IMAGE='image'
  VIDEO='video'
  URL='url'
  AUDIO='audio'
  FILE='file'

def contains_url(text):
    url_pattern = re.compile(
        r'^\s*http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\s*$   '
    )
    return bool(url_pattern.search(text))

def determine_media_type(bytes_io) -> MediaType:
    bytes_io.seek(0)         
    # Create a Magic object
    mime = magic.Magic(mime=True)
    
    # Determine the file type
    file_type = mime.from_buffer(bytes_io.getvalue())
    print(file_type)
    # Check the type
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
    

