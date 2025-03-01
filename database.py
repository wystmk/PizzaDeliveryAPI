# from sqlalchemy import create_engine
# from sqlalchemy.orm import  declarative_base,sessionmaker


# DATABASE_URL = "postgresql://wingyeeszeto@localhost/pizza_delivery"

# engine = create_engine(DATABASE_URL,
#     echo=True
# )

# Base=declarative_base()

# Session=sessionmaker()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session, declarative_base

DATABASE_URL = "postgresql://wingyeeszeto@localhost/pizza_delivery"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()