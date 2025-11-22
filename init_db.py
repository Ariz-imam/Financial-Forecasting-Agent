# init_db.py
from db.db import engine
from db.models import Base

print("Creating tables on DB:", engine.url)
Base.metadata.create_all(bind=engine)
print("Done.")
