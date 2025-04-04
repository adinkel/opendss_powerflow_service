from sqlmodel import create_engine
from sqlmodel import Session

from opendss_fastapi_celery.app.config.config import settings


engine = create_engine(settings.SQLALCHEMY_DATABASE_URI.unicode_string())

def get_db():
    with Session(engine) as session:
        yield session