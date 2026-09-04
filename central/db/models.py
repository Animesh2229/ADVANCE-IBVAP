from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True)
    hashed_password = Column(String(255))
    full_name = Column(String(100))
    role = Column(String(30), default="operator")  # admin, commander, operator, patroller
    is_active = Column(Boolean, default=True)
    fcm_token = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), index=True)
    alert_type = Column(String(50))
    subtype = Column(String(50), nullable=True)
    confidence = Column(Float)
    bbox = Column(JSON)
    track_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="new")
    priority = Column(String(20), default="LOW")
    raw_data = Column(JSON)
    event_hash = Column(String(64), nullable=True)

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"
    id = Column(Integer, primary_key=True)
    person_name = Column(String(100), nullable=True)
    embedding = Column(JSON)
    camera_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_watchlist = Column(Boolean, default=False)

class VehicleWatchlist(Base):
    __tablename__ = "vehicle_watchlist"
    id = Column(Integer, primary_key=True)
    plate_number = Column(String(20), unique=True, index=True)
    country = Column(String(10))
    vehicle_type = Column(String(30), nullable=True)
    owner_name = Column(String(100), nullable=True)
    status = Column(String(30), default="watch")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(50))

class ImmutableEvent(Base):
    __tablename__ = "immutable_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))
    data = Column(JSON)
    source = Column(String(50))
    prev_hash = Column(String(64))
    hash = Column(String(64), unique=True)
    signature = Column(String(200), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
