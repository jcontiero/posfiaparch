from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import configuracoes

engine = create_engine(configuracoes.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
