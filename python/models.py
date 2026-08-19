from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from database import Base


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)

    text_length = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False)

    category = Column(String(100), nullable=False)
    priority = Column(String(20), nullable=False)
    sentiment = Column(String(20), nullable=False)

    summary = Column(Text, nullable=False)
    action = Column(Text, nullable=False)