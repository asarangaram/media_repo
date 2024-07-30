from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create a SQLite database in memory (you can use a different database URL)
database_url = 'sqlite:///:memory:'
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)


Base.metadata.create_all(engine)
# Create a new user
new_user = User(username='john_doe', email='john@example.com')
session = Session()
session.add(new_user)
session.commit()

# Query for users
users = session.query(User).all()
for user in users:
    print(user.id, user.username, user.email)

# Update a user
user_to_update = session.query(User).filter_by(username='john_doe').first()
user_to_update.email = 'new_email@example.com'
session.commit()

# Delete a user
user_to_delete = session.query(User).filter_by(username='john_doe').first()
session.delete(user_to_delete)
session.commit()

session.close()
