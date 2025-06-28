import openai
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
        self.system_prompt = """Ты дружелюбный и полезный собеседник. Общайся естественно и по-человечески. 
Отвечай на русском языке, если пользователь пишет на русском. Помогай пользователю и поддерживай приятную беседу.
Будь вежливым, но не формальным. Можешь использовать эмодзи, но в меру."""

    async def get_response(self, user_message: str, conversation_context: List[Dict] = None) -> str:
        """Получить ответ от OpenAI GPT"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Добавляем контекст предыдущих сообщений
            if conversation_context:
                messages.extend(conversation_context)
            
            # Добавляем текущее сообщение пользователя
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return response.choices[0].message.content
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            return "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже."

    def set_system_prompt(self, prompt: str):
        """Изменить системный промпт"""
        self.system_prompt = prompt

    def set_model(self, model: str):
        """Изменить модель GPT"""
        self.model = model