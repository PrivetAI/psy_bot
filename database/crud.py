from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from .models import User, Message


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
        # Обновляем информацию о пользователе если она изменилась
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


async def save_message(db: AsyncSession, telegram_id: int, message_id: int,
                      user_message: str, bot_response: str, response_time_ms: int = None) -> Message:
    """Сохранить сообщение в базу данных"""
    message = Message(
        telegram_id=telegram_id,
        message_id=message_id,
        user_message=user_message,
        bot_response=bot_response,
        response_time_ms=response_time_ms
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_user_messages(db: AsyncSession, telegram_id: int, limit: int = 10) -> List[Message]:
    """Получить последние сообщения пользователя"""
    result = await db.execute(
        select(Message)
        .where(Message.telegram_id == telegram_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_conversation_context(db: AsyncSession, telegram_id: int, limit: int = 5) -> List[dict]:
    """Получить контекст последних сообщений для AI"""
    messages = await get_user_messages(db, telegram_id, limit)
    
    context = []
    for msg in reversed(messages):  # Обращаем порядок для хронологической последовательности
        context.extend([
            {"role": "user", "content": msg.user_message},
            {"role": "assistant", "content": msg.bot_response}
        ])
    
    return context