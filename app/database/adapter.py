from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config


class DatabaseAdapter:
    def __init__(self):
        self.engine = create_engine(Config.get_database_url())
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()