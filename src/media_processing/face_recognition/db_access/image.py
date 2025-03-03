from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text


class DBase(object):
    def __init__(self, uri):
        self.engine = create_engine(uri)
        self.Session = sessionmaker(bind=self.engine)

    def __enter__(self):
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()
        pass


class ImageDB(DBase):
    """This is a read-only table"""

    select_query = """ LIMIT 0, 20"""

    def get_images(self, limit=None, offset=None):
        query = "SELECT  id,path FROM images"
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"

        with self as db:
            result = self.session.execute(text(query))
            return [{"id": row[0], "path": row[1]} for row in result]
