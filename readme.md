# Telegram AI Bot

Telegram бот-собеседник на FastAPI с интеграцией OpenAI GPT и PostgreSQL для хранения истории диалогов.

## Возможности

- 🤖 AI-собеседник на базе OpenAI GPT-3.5-turbo
- 💾 Хранение истории диалогов в PostgreSQL
- 📝 Сохранение метаданных сообщений (время ответа, типы сообщений)
- 🔄 Контекст предыдущих сообщений для более естественного диалога
- 🐳 Полная контейнеризация с Docker
- 📊 Структурированное логирование

## Быстрый старт

### 1. Подготовка

1. Создайте бота в Telegram через [@BotFather](https://t.me/BotFather)
2. Получите API ключ от [OpenAI](https://platform.openai.com/api-keys)
3. Клонируйте репозиторий

### 2. Настройка переменных окружения

Скопируйте `.env` файл и заполните необходимые данные:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Запуск

```bash
# Запуск в Docker
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

## Структура проекта

```
telegram-ai-bot/
├── bot/
│   ├── __init__.py
│   └── handlers.py          # Обработчики Telegram команд и сообщений
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy модели
│   ├── database.py         # Настройка подключения к БД
│   └── crud.py             # Операции с базой данных
├── services/
│   ├── __init__.py
│   └── openai_service.py   # Сервис для работы с OpenAI API
├── logs/                   # Директория для логов
├── docker-compose.yml      # Docker Compose конфигурация
├── Dockerfile             # Docker образ приложения
├── requirements.txt       # Python зависимости
├── main.py               # Точка входа приложения
├── .env                  # Переменные окружения
└── README.md
```

## Команды бота

- `/start` - Приветствие и начало работы
- `/help` - Справка по использованию
- `/clear` - Очистка контекста диалога

## База данных

### Таблица `users`
- Хранит информацию о пользователях Telegram
- Автоматически создается при первом сообщении

### Таблица `messages`
- Хранит все диалоги пользователей с ботом
- Включает метаданные: время ответа, типы сообщений
- Используется для создания контекста в диалоге

## Настройка

### Изменение модели OpenAI

В файле `services/openai_service.py`