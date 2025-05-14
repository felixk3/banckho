from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base


engine = create_engine("sqlite:///banckho.db", echo=True)

#session = Session(engine)

Base.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session