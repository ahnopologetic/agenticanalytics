from db import SessionLocal
from fastapi import Request


def get_db(request: Request = None):
    """
    Get the database session. Uses db_session_factory from the test context if available, otherwise SessionLocal.
    Returns:
        Session
    """
    if request is not None and hasattr(request.app.state, "db_session_factory"):
        Session = request.app.state.db_session_factory
    else:
        Session = SessionLocal
    db = Session()
    try:
        yield db
    finally:
        db.close()
