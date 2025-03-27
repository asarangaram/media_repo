## hnsw index is handled here

from clmediakit import HNSWIndexDB
from .config import ConfigClass

hnsw_image_lookup = HNSWIndexDB(ConfigClass.HNSW_IMAGE_LOOKUP_LOCATION)
hnsw_video_lookup = HNSWIndexDB(ConfigClass.HNSW_VIDEO_LOOKUP_LOCATION)
