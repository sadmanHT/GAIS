import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan", uselist=False)


class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encoded_id = Column(Integer, unique=True, index=True)
    topic = Column(String(100), nullable=False)
    difficulty = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)

    interactions = relationship("Interaction", back_populates="question", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = 'interactions'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=False)
    question_id = Column(Uuid(as_uuid=True), ForeignKey('questions.id'), nullable=False)
    correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="interactions")
    question = relationship("Question", back_populates="interactions")


class KnowledgeState(Base):
    __tablename__ = 'knowledge_states'
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=False)
    concept = Column(String(100), nullable=False)
    mastery_probability = Column(Float, nullable=False, default=0.0)
    engagement_score = Column(Float, nullable=False, default=0.5)
    confusion_score = Column(Float, nullable=False, default=0.0)
    retention_score = Column(Float, nullable=False, default=0.5)
    recent_accuracy = Column(Float, nullable=False, default=0.5)
    review_count = Column(Integer, nullable=False, default=1)
    questions_answered = Column(Integer, nullable=False, default=0)
    incorrect_streak = Column(Integer, nullable=False, default=0)
    session_time_minutes = Column(Float, nullable=False, default=0.0)
    last_reviewed_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="knowledge_states")


class UserSettings(Base):
    __tablename__ = 'user_settings'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    time_pressure = Column(Boolean, nullable=False, default=True)
    audio_cues = Column(Boolean, nullable=False, default=True)
    daily_session_minutes = Column(Integer, nullable=False, default=25)
    weekly_summary = Column(Boolean, nullable=False, default=True)
    target_score = Column(Integer)
    test_date = Column(String(100))
    weakest_area = Column(String(100))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="settings")
