from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import config

engine = create_engine(config.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 