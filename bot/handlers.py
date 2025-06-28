import time
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.database import AsyncSessionLocal
from database.crud import (
    get_or_create_user, save_message, get_conversation_context,
    get_or_create_active_session, get_or_create_client_profile,
    update_client_profile, clear_user_history
)
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
openai_service = OpenAIService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = f"""Здравствуйте, {user.first_name}! 🌟

/start - старт бота 
/finishsession #todo закончить сессию(вернуть саммари сессии пациенту, обновить профиль пациента)
/help - информация о работе с ботом
/clear - удалить все данные обо мне"""

новая сессия начинается при отправке нового сообщения. 