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
    welcome_message = f"""Здравствуйте, {user.first_name}! 🌟

Я ваш персональный психолог-консультант. Здесь вы можете:
• Поделиться своими переживаниями и мыслями
• Получить эмоциональную поддержку  
• Разобрать сложные жизненные ситуации
• Найти новые способы решения проблем

Наша беседа конфиденциальна. Расскажите, что вас беспокоит сегодня?

Команды:
/start - начать сессию
/help - информация о работе с ботом
/clear - начать новую сессию (очистить контекст)"""

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
    help_text = """🧠 Как проходит психологическая консультация:

• Я выслушаю вас без осуждения
• Помогу разобрать ваши чувства и мысли  
• Задам вопросы для лучшего понимания ситуации
• Направлю к осознанию собственных решений
• Поддержу в трудные моменты

💡 Советы для эффективной работы:
• Будьте честны с собой и со мной
• Описывайте свои чувства подробно
• Не бойтесь говорить о болезненных темах
• Задавайте вопросы, если что-то непонятно

⚠️ Важно помнить:
• При острых кризисных состояниях обращайтесь к специалистам
• Бот не заменяет очную психотерапию
• В экстренных случаях звоните на горячие линии помощи

Команды:
/clear - начать новую сессию
/help - эта справка"""

    await update.message.reply_text(help_text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clear для начала новой сессии"""
    await update.message.reply_text(
        "✨ Начинаем новую сессию с чистого листа.\n\n"
        "Расскажите, что сейчас происходит в вашей жизни? "
        "Какие мысли или чувства вас беспокоят?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    message_id = update.message.message_id
    
    logger.info(f"Сообщение от {user.username} ({user.id}): {len(user_message)} символов")
    
    # Показываем что психолог "думает"
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
            
            # Получаем контекст предыдущих сообщений (последние 20 для поддержания контекста сессии)
            conversation_context = await get_conversation_context(db, user.id, limit=20)
            
            # Получаем ответ психолога от OpenAI
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
            "Извините, произошла техническая ошибка. "
            "Давайте попробуем продолжить нашу беседу. "
            "Можете повторить ваш вопрос?"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Если есть update и это сообщение, отвечаем пользователю
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла техническая ошибка, но я все еще здесь и готов вас выслушать. "
            "Попробуйте написать еще раз."
        )