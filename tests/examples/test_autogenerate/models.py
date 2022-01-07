from sqlalchemy import Column, Integer

from strapp.sqlalchemy import declarative_base

Base = declarative_base()


class Foo(Base, created_at=True, updated_at=True):
    __tablename__ = "asdf"

    id = Column(Integer, primary_key=True)
