# db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    request_json = Column(Text)
    response_json = Column(Text)
    status = Column(String(50), default="pending")
