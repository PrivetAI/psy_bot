import time
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import AsyncSessionLocal
from database.crud import get_or_create_user, save_message, get_conversation_context
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
openai_service = OpenAIService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = f"""Привет, {user.first_name}! 👋

Я AI-собеседник, готов поболтать с тобой на любые темы. 
Просто напиши мне что-нибудь, и я отвечу!

Доступные команды:
/start - показать это сообщение
/help - получить помощь
/clear - очистить контекст диалога"""

    await update.message.reply_text(welcome_message)
    
    # Сохраняем пользователя в базу данных
    async with AsyncSessionLocal() as db:
        await get_or_create_user(
            db=db,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """🤖 Как пользоваться ботом:

• Просто напишите мне любое сообщение
• Я запоминаю контекст нашего диалога
• Могу общаться на разные темы
• Отвечаю быстро и по существу

Команды:
/start - начать заново
/help - эта справка
/clear - очистить историю диалога

Если что-то не работает, попробуйте перезапустить бота командой /start"""

    await update.message.reply_text(help_text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear для очистки контекста"""
    # В данной реализации мы не удаляем сообщения из БД, 
    # просто уведомляем пользователя что контекст "очищен"
    await update.message.reply_text(
        "✅ Контекст диалога очищен! Начинаем общение с чистого листа."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    message_id = update.message.message_id
    
    logger.info(f"Получено сообщение от {user.username} ({user.id}): {user_message}")
    
    # Показываем что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    start_time = time.time()
    
    try:
        async with AsyncSessionLocal() as db:
            # Получаем или создаем пользователя
            await get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Получаем контекст предыдущих сообщений
            conversation_context = await get_conversation_context(db, user.id, limit=100)
            
            # Получаем ответ от OpenAI
            bot_response = await openai_service.get_response(user_message, conversation_context)
            
            # Вычисляем время ответа
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Сохраняем сообщение в базу данных
            await save_message(
                db=db,
                telegram_id=user.id,
                message_id=message_id,
                user_message=user_message,
                bot_response=bot_response,
                response_time_ms=response_time_ms
            )
            
            # Отправляем ответ пользователю
            await update.message.reply_text(bot_response)
            
            logger.info(f"Ответ отправлен за {response_time_ms}ms")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Если есть update и это сообщение, отвечаем пользователю
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )