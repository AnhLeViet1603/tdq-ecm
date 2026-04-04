.PHONY: help up down build logs ps migrate-all createsuperuser-auth shell-% restart-%

# Default target
help:
	@echo "E-Commerce Microservices - Available Commands:"
	@echo ""
	@echo "  make up              Start all services (detached)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild all Docker images"
	@echo "  make logs            Tail logs from all services"
	@echo "  make logs-<svc>      Tail logs from specific service (e.g. make logs-auth)"
	@echo "  make ps              Show running containers"
	@echo "  make migrate-all     Run migrations for all Django services"
	@echo "  make shell-<svc>     Open Django shell (e.g. make shell-auth)"
	@echo "  make restart-<svc>   Restart a specific service"
	@echo "  make clean           Remove volumes and containers"

# ── Docker Compose ────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-%:
	docker compose logs -f $*

ps:
	docker compose ps

restart-%:
	docker compose restart $*

clean:
	docker compose down -v --remove-orphans

# ── Migrations ────────────────────────────────────────────────
SERVICES = auth product inventory cart order payment promotion review shipping

migrate-all:
	@for svc in $(SERVICES); do \
		echo ">>> Migrating $$svc..."; \
		docker compose exec $$svc python manage.py migrate --noinput; \
	done

makemigrations-%:
	docker compose exec $* python manage.py makemigrations

migrate-%:
	docker compose exec $* python manage.py migrate --noinput

# ── Django Shell ──────────────────────────────────────────────
shell-%:
	docker compose exec $* python manage.py shell

# ── Superuser ─────────────────────────────────────────────────
createsuperuser-auth:
	docker compose exec auth python manage.py createsuperuser
