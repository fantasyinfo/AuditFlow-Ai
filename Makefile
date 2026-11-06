.PHONY: up down build test lint migrate seed-demo

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

test:
	pytest tests/ -v

lint:
	ruff check .

migrate:
	alembic upgrade head

seed-demo:
	python scripts/seed_demo_data.py

