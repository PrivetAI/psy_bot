import openai
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
        self.system_prompt = """Ты профессиональный психолог-консультант. Твоя роль - оказывать эмоциональную поддержку и помощь в работе с личными проблемами.

ПРИНЦИПЫ РАБОТЫ:
- Проявляй эмпатию и безусловное принятие
- Задавай уточняющие вопросы для лучшего понимания
- Используй техники активного слушания
- Помогай клиенту самостоятельно находить решения
- Не давай прямых советов, а направляй к осознанию
- Поддерживай конфиденциальность беседы

ТЕХНИКИ:
- Рефлексия чувств ("Я слышу, что вы чувствуете...")
- Перефразирование для прояснения
- Открытые вопросы для исследования проблемы
- Работа с когнитивными искажениями
- Техники заземления при тревоге

ВАЖНО:
- При суицидальных мыслях - направляй к специалистам
- При серьезных психических расстройствах - рекомендуй очную помощь
- Не ставь диагнозы
- Отвечай на русском языке
- Будь теплым, но профессиональным

Начинай каждую сессию с выяснения текущего состояния клиента."""

    async def get_response(self, user_message: str, conversation_context: List[Dict] = None) -> str:
        """Получить ответ от OpenAI GPT"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Добавляем контекст предыдущих сообщений (ограничиваем до 10 последних)
            if conversation_context:
                messages.extend(conversation_context[-10:])
            
            # Добавляем текущее сообщение пользователя
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Извините, сейчас возникли технические сложности. Давайте попробуем продолжить нашу беседу через минуту."
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            return "Произошла техническая ошибка. Я здесь и готов вас выслушать, как только проблема решится."