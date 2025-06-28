.PHONY: help build up down logs restart clean db-shell

help:
	@echo "Доступные команды:"
	@echo "  build    - Собрать Docker образы"
	@echo "  up       - Запустить приложение"
	@echo "  down     - Остановить приложение"
	@echo "  logs     - Показать логи"
	@echo "  restart  - Перезапустить приложение"
	@echo "  clean    - Очистить Docker ресурсы"
	@echo "  db-shell - Подключиться к базе данных"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f bot

restart: down up

clean:
	docker-compose down -v
	docker system prune -f

db-shell:
	docker-compose exec postgres psql -U bot_user -d telegram_bot