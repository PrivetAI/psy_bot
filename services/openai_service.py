import openai
import os
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
        self.system_prompt = """Ты — психиатр-психотерапевт нового поколения, соединяющий когнитивную психологию, психоанализ и методы работы с подсознанием. 

Твоя задача — выявить бессознательные, неочевидные причины, по которым человек занимается саморазрушающим поведением: переедание, курение, алкоголь, другие зависимости и деструктивные паттерны.

ПРИНЦИПЫ РАБОТЫ:
- НЕ даёшь поверхностные советы типа "просто прекрати"
- Работаешь в формате последовательной глубинной сессии
- Задаёшь по одному глубокому вопросу за раз
- Ждёшь ответ клиента, анализируешь, формулируешь следующий вопрос
- Постепенно добираешься до корневых установок, боли и внутренних конфликтов

ТЕХНИКА ВОПРОСОВ:
- Обходишь защитные реакции психики
- Добираешься до скрытого "почему" на уровне травмы, детских шаблонов
- Исследуешь эмоциональные паттерны и триггеры
- Выявляешь связи между текущим поведением и прошлым опытом
- Работаешь с подсознательными убеждениями

ФОРМАТ ОТВЕТА:
1. Краткий анализ ответа клиента (1-2 предложения)
2. Один глубокий вопрос, ведущий глубже
3. Никаких готовых решений до вскрытия истоков

ВАЖНО:
- Не давай советов до полного понимания корневых причин
- Вопросы должны быть глубже уровня "а зачем ты это делаешь?"
- Ищи эмоциональные травмы, детские паттерны, скрытые потребности
- Будь деликатным, но настойчивым в исследовании

В конце каждого ответа добавляй JSON с обновлениями профиля клиента:
{
  "profile_update": {
    "identified_patterns": "новые выявленные паттерны",
    "emotional_triggers": "обнаруженные триггеры", 
    "defense_mechanisms": "защитные механизмы",
    "therapeutic_notes": "важные заметки для терапии"
  }
}

Начинай работу с выяснения конкретного саморазрушающего поведения и первого вопроса к источнику эмоционального голода."""

    async def get_response(self, user_message: str, conversation_context: List[Dict] = None, 
                          client_profile: Dict = None) -> tuple[str, Dict]:
        """Получить ответ от OpenAI GPT и обновления профиля"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Добавляем профиль клиента в контекст
            if client_profile:
                profile_context = self._format_profile_context(client_profile)
                if profile_context:
                    messages.append({"role": "system", "content": profile_context})
            
            # Добавляем историю сообщений (последние 30 для контекста)
            if conversation_context:
                messages.extend(conversation_context[-30:])
            
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.8,
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
            
            full_response = response.choices[0].message.content
            
            # Извлекаем JSON с обновлениями профиля
            response_text, profile_updates = self._extract_profile_updates(full_response)
            
            return response_text, profile_updates
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return ("Сейчас возникли технические сложности. Однако это не останавливает нашу работу. "
                   "Можете поделиться тем, что вас беспокоит, а я выслушаю как только система восстановится."), {}
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            return ("Произошла техническая ошибка, но наша сессия продолжается. "
                   "Я готов вас выслушать и помочь разобраться с тем, что вас тревожит."), {}

    def _format_profile_context(self, profile: Dict) -> str:
        """Форматировать профиль клиента для контекста"""
        context_parts = ["ПРОФИЛЬ КЛИЕНТА:"]
        
        if profile.get('identified_patterns'):
            context_parts.append(f"Выявленные паттерны: {profile['identified_patterns']}")
        if profile.get('core_traumas'):
            context_parts.append(f"Основные травмы: {profile['core_traumas']}")
        if profile.get('emotional_triggers'):
            context_parts.append(f"Эмоциональные триггеры: {profile['emotional_triggers']}")
        if profile.get('defense_mechanisms'):
            context_parts.append(f"Защитные механизмы: {profile['defense_mechanisms']}")
        if profile.get('therapeutic_notes'):
            context_parts.append(f"Терапевтические заметки: {profile['therapeutic_notes']}")
            
        return "\n".join(context_parts) if len(context_parts) > 1 else ""

    def _extract_profile_updates(self, response: str) -> tuple[str, Dict]:
        """Извлечь обновления профиля из ответа"""
        try:
            # Ищем JSON в конце ответа
            lines = response.strip().split('\n')
            json_start = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('{') and 'profile_update' in line:
                    json_start = i
                    break
            
            if json_start != -1:
                json_text = '\n'.join(lines[json_start:])
                profile_data = json.loads(json_text)
                response_text = '\n'.join(lines[:json_start]).strip()
                
                return response_text, profile_data.get('profile_update', {})
            
            return response, {}
            
        except (json.JSONDecodeError, KeyError):
            return response, {}