
import uuid

_info = """
This API service offers microservices through a RESTful interface. \
Please refer to the appropriate endpoint that aligns with your specific needs. \
Consult the API documentation or relevant resources to identify the correct endpoints for the functionalities you require.
""".strip()


class LandingPageModel:
    def __init__(self, name='colan_server'):
        self.name = name
        self.info = _info
        self.id = uuid.getnode()
