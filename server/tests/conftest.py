import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config
from db_models import Base


@pytest.fixture(scope="session")
def config_for_test():
    config.db_url = "sqlite:///./test.db?check_same_thread=False&cache=shared"
    config.env = "test"
    yield config


@pytest.fixture(scope="function")
def db(config_for_test):
    engine = create_engine(config_for_test.db_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session_factory(db):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db)
    yield SessionLocal


@pytest.fixture(scope="function")
def db_session(db_session_factory):
    session = db_session_factory()
    yield session

    session.rollback()
    session.close()
