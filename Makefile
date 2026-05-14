.PHONY: help up down build logs logs-backend logs-frontend logs-db test test-e2e migrate shell db-reset status

PROJECT := accounting-ai
DC := sg docker -c "docker compose -p $(PROJECT)"

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-12s$(NC) %s\n", $$1, $$2}'

# ── Docker Compose ───────────────────────────────────────────────────────────

up: ## Start all services
	$(DC) up -d --build

down: ## Stop all services (keep volumes)
	$(DC) down

build: ## Rebuild all services
	$(DC) up -d --build

status: ## Show container status
	$(DC) ps

# ── Logs ─────────────────────────────────────────────────────────────────────

logs: ## Tail all logs
	$(DC) logs -f

logs-backend: ## Tail backend logs
	$(DC) logs -f backend

logs-frontend: ## Tail frontend logs
	$(DC) logs -f frontend

logs-db: ## Tail database logs
	$(DC) logs -f db

# ── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run alembic migrations
	$(DC) exec backend alembic upgrade head

migrate-redo: ## Rollback last migration and re-run
	$(DC) exec backend alembic downgrade -1
	$(DC) exec backend alembic upgrade head

db-reset: ## Stop services, remove volumes, start fresh
	$(DC) down -v
	$(DC) up -d
	$(DC) exec backend alembic upgrade head

db-shell: ## Open psql shell
	$(DC) exec db psql -U postgres -d accounting

# ── Tests ─────────────────────────────────────────────────────────────────────

test: ## Run backend pytest
	$(DC) exec backend pytest -v

test-watch: ## Run backend pytest with watch mode
	$(DC) exec backend pytest -v --watch

test-e2e: ## Run frontend E2E tests (Playwright)
	cd frontend && npm run test:e2e

test-e2e-ui: ## Open Playwright UI mode
	cd frontend && npx playwright test --ui

# ── Shell ─────────────────────────────────────────────────────────────────────

shell-backend: ## Get shell in backend container
	$(DC) exec backend /bin/sh

shell-frontend: ## Get shell in frontend container
	$(DC) exec frontend /bin/sh

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean: ## Remove stopped containers and dangling images
	$(DC) down --remove-orphans
	docker image prune -f

prune: ## Remove all containers, volumes, and images for this project
	$(DC) down -v --remove-orphans
	docker volume prune -f
