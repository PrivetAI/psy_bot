from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    message_id = Column(Integer, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    session_id = Column(String(50), nullable=False)  # ID сессии
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message_type = Column(String(50), default="text")
    response_time_ms = Column(Integer, nullable=True)


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    
    # Основная информация
    identified_patterns = Column(Text, nullable=True)  # Выявленные паттерны
    core_traumas = Column(Text, nullable=True)  # Основные травмы
    emotional_triggers = Column(Text, nullable=True)  # Эмоциональные триггеры
    defense_mechanisms = Column(Text, nullable=True)  # Защитные механизмы
    
    # Прогресс
    breakthrough_moments = Column(Text, nullable=True)  # Моменты прорыва
    resistance_areas = Column(Text, nullable=True)  # Области сопротивления
    therapeutic_notes = Column(Text, nullable=True)  # Терапевтические заметки
    
    # Метаданные
    sessions_count = Column(Integer, default=0)
    last_session_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TherapySession(Base):
    __tablename__ = "therapy_sessions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, index=True, nullable=False)
    session_id = Column(String(50), unique=True, nullable=False)
    
    # Сессия
    session_focus = Column(Text, nullable=True)  # Фокус сессии
    key_insights = Column(Text, nullable=True)  # Ключевые инсайты
    emotional_state_start = Column(String(100), nullable=True)  # Состояние в начале
    emotional_state_end = Column(String(100), nullable=True)  # Состояние в конце
    
    # Метаданные
    messages_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)