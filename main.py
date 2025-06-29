import asyncio
import os
import logging
import signal
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database.database import init_db
from bot.handlers import (
    start_command, help_command, clear_command, 
    finish_session_command, handle_message, error_handler
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция приложения"""
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    if not openai_key:
        logger.error("OPENAI_API_KEY не установлен!")
        return
    
    logger.info("Инициализация базы данных...")
    try:
        await init_db()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return
    
    logger.info("Создание Telegram бота...")
    application = Application.builder().token(telegram_token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("finishsession", finish_session_command))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Инициализируем приложение
    await application.initialize()
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        await application.start()
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
        stop_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, останавливаем бота...")
            stop_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        await stop_event.wait()
        
    except Exception as e:
        logger.error(f"Ошибка в работе бота: {e}")
    finally:
        logger.info("Остановка бота...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")