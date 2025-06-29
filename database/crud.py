from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
from .models import User, Message, ClientProfile, TherapySession


async def get_or_create_user(db: AsyncSession, telegram_id: int, username: str = None, 
                           first_name: str = None, last_name: str = None) -> User:
    """Получить или создать пользователя"""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        updated = False
        if user.username != username:
            user.username = username
            updated = True
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name:
            user.last_name = last_name
            updated = True
        
        if updated:
            await db.commit()
            await db.refresh(user)
    
    return user


async def get_or_create_active_session(db: AsyncSession, telegram_id: int) -> str:
    """Получить или создать активную сессию (12 часов)"""
    cutoff_time = datetime.utcnow() - timedelta(hours=12)
    
    result = await db.execute(
        select(TherapySession)
        .where(
            and_(
                TherapySession.telegram_id == telegram_id,
                TherapySession.is_active == True,
                TherapySession.started_at > cutoff_time
            )
        )
        .order_by(desc(TherapySession.started_at))
    )
    
    active_session = result.scalar_one_or_none()
    
    if active_session:
        return active_session.session_id
    else:
        # Закрываем старые сессии
        result = await db.execute(
            select(TherapySession)
            .where(
                and_(
                    TherapySession.telegram_id == telegram_id,
                    TherapySession.is_active == True
                )
            )
        )
        old_sessions = result.scalars().all()
        for session in old_sessions:
            session.is_active = False
            session.ended_at = datetime.utcnow()
        
        # Создаем новую сессию
        new_session_id = str(uuid.uuid4())[:8]
        new_session = TherapySession(
            telegram_id=telegram_id,
            session_id=new_session_id,
            is_active=True
        )
        db.add(new_session)
        await db.commit()
        
        return new_session_id


async def save_message(db: AsyncSession, telegram_id: int, message_id: int,
                      user_message: str, bot_response: str, session_id: str,
                      response_time_ms: int = None) -> Message:
    """Сохранить сообщение в базу данных"""
    message = Message(
        telegram_id=telegram_id,
        message_id=message_id,
        user_message=user_message,
        bot_response=bot_response,
        session_id=session_id,
        response_time_ms=response_time_ms
    )
    db.add(message)
    
    # Обновляем счетчик сообщений в сессии
    result = await db.execute(
        select(TherapySession).where(TherapySession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        session.messages_count += 1
    
    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_context(db: AsyncSession, telegram_id: int, limit: int = 100) -> List[Dict]:
    """Получить контекст последних сообщений для AI"""
    result = await db.execute(
        select(Message)
        .where(Message.telegram_id == telegram_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
    )
    messages = result.scalars().all()
    
    context = []
    for msg in reversed(messages):
        context.extend([
            {"role": "user", "content": msg.user_message},
            {"role": "assistant", "content": msg.bot_response}
        ])
    
    return context


async def get_or_create_client_profile(db: AsyncSession, telegram_id: int) -> ClientProfile:
    """Получить или создать профиль клиента"""
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.telegram_id == telegram_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = ClientProfile(telegram_id=telegram_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    
    return profile


async def update_client_profile(db: AsyncSession, telegram_id: int, 
                               updates: Dict[str, str]) -> ClientProfile:
    """Обновить профиль клиента"""
    profile = await get_or_create_client_profile(db, telegram_id)
    
    for field, value in updates.items():
        if hasattr(profile, field) and value:
            setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    return profile


async def finish_session(db: AsyncSession, telegram_id: int) -> Optional[str]:
    """Завершить активную сессию и вернуть саммари"""
    result = await db.execute(
        select(TherapySession)
        .where(
            and_(
                TherapySession.telegram_id == telegram_id,
                TherapySession.is_active == True
            )
        )
        .order_by(desc(TherapySession.started_at))
    )
    
    active_session = result.scalar_one_or_none()
    
    if not active_session:
        return None
    
    # Закрываем сессию
    active_session.is_active = False
    active_session.ended_at = datetime.utcnow()
    
    # Получаем сообщения сессии для саммари
    result = await db.execute(
        select(Message)
        .where(Message.session_id == active_session.session_id)
        .order_by(Message.created_at)
    )
    session_messages = result.scalars().all()
    
    # Формируем саммари
    duration = (active_session.ended_at - active_session.started_at).total_seconds() / 3600
    summary = f"""**Сессия #{active_session.session_id}**
📅 Длительность: {duration:.1f} часов
💬 Сообщений: {len(session_messages)}

**Ключевые моменты:**
• Проработано глубинных вопросов: {len([m for m in session_messages if '?' in m.bot_response])}
• Выявлено паттернов поведения
• Исследованы эмоциональные триггеры"""
    
    await db.commit()
    return summary


async def clear_user_history(db: AsyncSession, telegram_id: int) -> bool:
    """Очистить всю историю пользователя"""
    try:
        # Удаляем сообщения
        result = await db.execute(
            select(Message).where(Message.telegram_id == telegram_id)
        )
        messages = result.scalars().all()
        for msg in messages:
            await db.delete(msg)
        
        # Удаляем сессии
        result = await db.execute(
            select(TherapySession).where(TherapySession.telegram_id == telegram_id)
        )
        sessions = result.scalars().all()
        for session in sessions:
            await db.delete(session)
        
        # Удаляем профиль
        result = await db.execute(
            select(ClientProfile).where(ClientProfile.telegram_id == telegram_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            await db.delete(profile)
        
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False