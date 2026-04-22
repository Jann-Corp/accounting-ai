.PHONY: help up down build rebuild logs logs-backend logs-db restart ps clean \
        test test-e2e test-all dev dev-frontend \
        install install-backend install-frontend \
        migrate db-reset db-shell \
        lint format \
        logs-api

# ==================== Docker ====================
DOCKER := sg docker -c "docker compose"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all services (docker compose up -d)
	$(DOCKER) up -d

down: ## Stop all services
	$(DOCKER) down

restart: ## Restart all services
	$(DOCKER) restart

build: ## Build images without cache
	$(DOCKER) build --pull --no-cache

rebuild: ## Rebuild and restart (useful after code changes)
	$(DOCKER) build --pull
	$(DOCKER) up -d --force-recreate

ps: ## Show running containers
	$(DOCKER) ps

clean: ## Remove containers, volumes, and images
	$(DOCKER) down -v --rmi all

# ==================== Logs ====================
logs: ## Show all logs (follow mode)
	$(DOCKER) logs --tail=100 -f

logs-backend: ## Show backend logs only
	$(DOCKER) logs --tail=100 -f backend

logs-db: ## Show database logs only
	$(DOCKER) logs --tail=100 -f db

logs-api: ## Show backend API logs (alias)
	$(DOCKER) logs --tail=100 -f backend

# ==================== Development ====================
dev: ## Run backend locally (uvicorn with reload)
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Run frontend dev server (Vite)
	cd frontend && npm run dev

# ==================== Testing ====================
test: ## Run backend pytest
	cd backend && source venv/bin/activate && pytest -q

test-e2e: ## Run Playwright E2E tests
	cd frontend && npx playwright test

test-all: test test-e2e ## Run all tests (backend + E2E)

# ==================== Dependencies ====================
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies (pip install)
	cd backend && source venv/bin/activate && pip install -r requirements.txt -q

install-frontend: ## Install frontend dependencies (npm install)
	cd frontend && npm install

# ==================== Database ====================
migrate: ## Run Alembic migrations (if configured)
	cd backend && source venv/bin/activate && alembic upgrade head || echo "No migrations configured"

db-reset: ## WARNING: Drop and recreate all database volumes
	@echo "⚠️  This will DELETE all data!"
	$(DOCKER) down -v
	$(DOCKER) up -d db

db-shell: ## Connect to PostgreSQL shell (psql)
	$(DOCKER) exec -it db psql -U postgres -d accounting

# ==================== Code Quality ====================
lint: ## Run linters (backend: ruff/flake8, frontend: eslint)
	cd backend && source venv/bin/activate && ruff check . || echo "ruff not installed"
	cd frontend && npx eslint . --ext .ts,.vue || echo "eslint not configured"

format: ## Format code (backend: ruff format, frontend: prettier)
	cd backend && source venv/bin/activate && ruff format . || echo "ruff not installed"
	cd frontend && npx prettier --write "src/**/*.{ts,vue}" || echo "prettier not configured"

# ==================== Quick Start ====================
setup: install build up ## Full setup: install deps, build, and start services
	@echo "✅ Setup complete! Frontend: http://localhost:3000, Backend: http://localhost:8000"
