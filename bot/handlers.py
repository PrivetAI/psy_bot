import time
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import AsyncSessionLocal
from database.crud import (
    get_or_create_user, save_message, get_conversation_context,
    get_or_create_active_session, get_or_create_client_profile,
    update_client_profile, clear_user_history, finish_session
)
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
openai_service = OpenAIService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = f"""Здравствуйте, {user.first_name}! 🌟

Я ваш персональный психотерапевт-консультант. Готов помочь разобраться в глубинных причинах деструктивных паттернов поведения и найти путь к внутренней гармонии.

Доступные команды:
/start - перезапустить бота
/finishsession - завершить текущую сессию и получить саммари
/help - информация о работе с ботом  
/clear - удалить все данные обо мне

Новая сессия начинается автоматически при отправке сообщения."""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_message = """🔍 **Как работает терапия:**

Я помогаю выявить неосознанные причины саморазрушающего поведения через глубинные вопросы. Работаю поэтапно:

1. **Выявление паттерна** - что именно вас беспокоит
2. **Поиск триггеров** - что запускает деструктивное поведение  
3. **Анализ корней** - связь с детскими травмами, установками
4. **Работа с подсознанием** - вскрытие скрытых потребностей

**Команды:**
• `/start` - начать заново
• `/finishsession` - завершить сессию с саммари
• `/clear` - удалить всю историю
• `/help` - эта справка

**Принципы работы:**
✓ Один глубокий вопрос за раз
✓ Никаких поверхностных советов
✓ Фокус на эмоциональных корнях проблемы
✓ Деликатная работа с защитными механизмами

Поделитесь тем, что вас беспокоит - начнём исследование."""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear"""
    async with AsyncSessionLocal() as db:
        success = await clear_user_history(db, update.effective_user.id)
        
        if success:
            message = """✅ Все ваши данные успешно удалены:

• История сообщений
• Сессии терапии  
• Профиль клиента
• Аналитические данные

Можете начать с чистого листа командой /start"""
        else:
            message = "❌ Произошла ошибка при удалении данных. Попробуйте позже."
    
    await update.message.reply_text(message)


async def finish_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /finishsession"""
    user_id = update.effective_user.id
    
    async with AsyncSessionLocal() as db:
        try:
            session_summary = await finish_session(db, user_id)
            
            if session_summary:
                summary_message = f"""🎯 **Саммари сессии:**

{session_summary}

Сессия завершена. При следующем сообщении начнётся новая сессия."""
            else:
                summary_message = "📝 Активная сессия не найдена или уже завершена."
                
        except Exception as e:
            logger.error(f"Ошибка завершения сессии для {user_id}: {e}")
            summary_message = "❌ Произошла ошибка при завершении сессии."
    
    await update.message.reply_text(summary_message, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    start_time = time.time()
    
    async with AsyncSessionLocal() as db:
        try:
            # Получаем/создаем пользователя
            db_user = await get_or_create_user(
                db, user.id, user.username, user.first_name, user.last_name
            )
            
            # Получаем активную сессию
            session_id = await get_or_create_active_session(db, user.id)
            
            # Получаем профиль клиента
            client_profile = await get_or_create_client_profile(db, user.id)
            profile_dict = {
                'identified_patterns': client_profile.identified_patterns,
                'core_traumas': client_profile.core_traumas,
                'emotional_triggers': client_profile.emotional_triggers,
                'defense_mechanisms': client_profile.defense_mechanisms,
                'breakthrough_moments': client_profile.breakthrough_moments,
                'resistance_areas': client_profile.resistance_areas,
                'therapeutic_notes': client_profile.therapeutic_notes
            }
            
            # Получаем контекст беседы
            context_messages = await get_conversation_context(db, user.id, limit=20)
            
            # Получаем ответ от OpenAI
            bot_response, profile_updates = await openai_service.get_response(
                user_message, context_messages, profile_dict
            )
            
            # Обновляем профиль клиента
            if profile_updates:
                await update_client_profile(db, user.id, profile_updates)
            
            # Сохраняем сообщение
            response_time = int((time.time() - start_time) * 1000)
            await save_message(
                db, user.id, update.message.message_id,
                user_message, bot_response, session_id, response_time
            )
            
            await update.message.reply_text(bot_response)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения от {user.id}: {e}")
            await update.message.reply_text(
                "Произошла техническая ошибка, но наша сессия продолжается. "
                "Я готов вас выслушать и помочь разобраться с тем, что вас тревожит."
            )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в боте: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла техническая ошибка. Я уже работаю над её устранением. "
                "Попробуйте повторить запрос через несколько минут."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}"))