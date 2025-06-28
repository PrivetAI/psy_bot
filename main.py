import asyncio
import os
import logging
import signal
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database.database import init_db
from bot.handlers import start_command, help_command, clear_command, handle_message, error_handler

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Глобальная переменная для приложения
application = None


async def setup_application():
    """Настройка и инициализация приложения"""
    global application
    
    # Проверяем наличие необходимых переменных окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
    
    if not openai_key:
        logger.error("OPENAI_API_KEY не установлен!")
        raise ValueError("OPENAI_API_KEY не установлен!")
    
    logger.info("Инициализация базы данных...")
    try:
        await init_db()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise
    
    # Создаем приложение Telegram бота
    logger.info("Создание Telegram бота...")
    application = Application.builder().token(telegram_token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    return application


async def shutdown_application():
    """Корректное завершение работы приложения"""
    global application
    if application:
        logger.info("Остановка бота...")
        await application.stop()
        await application.shutdown()


def main():
    """Основная функция приложения"""
    async def run_bot():
        try:
            app = await setup_application()
            
            # Настройка обработки сигналов
            def signal_handler(signum, frame):
                logger.info(f"Получен сигнал {signum}, останавливаем бота...")
                asyncio.create_task(shutdown_application())
                raise KeyboardInterrupt()
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # Запускаем бота
            logger.info("Бот запущен и готов к работе!")
            await app.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
                close_loop=False
            )
            
        except Exception as e:
            logger.error(f"Ошибка в работе бота: {e}")
            await shutdown_application()
            raise
    
    # Запуск
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()