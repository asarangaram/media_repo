# wsgi.py

from .app_factory import create_app
from .config import ConfigClass

app = create_app(ConfigClass)

if __name__ == '__main__':
    app.run(debug=True,)
