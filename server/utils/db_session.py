from db import SessionLocal


def get_db():
    """
    Get the database session.
    Returns:
        Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 