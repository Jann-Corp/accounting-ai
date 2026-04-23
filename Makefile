.PHONY: help up down stop start restart build rebuild logs logs-all logs-backend logs-frontend logs-db \
        ps status clean clean-all \
        test test-backend test-frontend test-e2e test-all test-coverage test-watch \
        dev dev-backend dev-frontend \
        install install-backend install-frontend \
        migrate migrate-create db-reset db-shell db-init \
        lint lint-backend lint-frontend format format-backend format-frontend \
        setup init check-env doctor backup restore \
        deploy deploy-prod

# ==================== Configuration ====================
DOCKER := docker compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend
ENV_FILE := .env

# Default target
.DEFAULT_GOAL := help

# ==================== Help ====================
help: ## Show this help message
	@echo "📊 Accounting AI - Makefile Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Quick Start: make setup"

# ==================== Environment Checks ====================
check-env: ## Check if .env file exists, copy from .env.example if not
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "📝 Creating .env from .env.example..."; \
		cp .env.example $(ENV_FILE); \
	else \
		echo "✅ .env file already exists"; \
	fi

doctor: check-env ## Run system diagnostics
	@echo "🔍 Running diagnostics..."
	@command -v docker >/dev/null 2>&1 && echo "✅ Docker: $(shell docker --version)" || echo "❌ Docker not installed"
	@command -v docker-compose >/dev/null 2>&1 && echo "✅ Docker Compose: $(shell docker-compose --version 2>/dev/null || docker compose version 2>/dev/null | head -1)" || echo "⚠️  Docker Compose not found"
	@command -v python3 >/dev/null 2>&1 && echo "✅ Python: $(shell python3 --version)" || echo "❌ Python3 not installed"
	@command -v node >/dev/null 2>&1 && echo "✅ Node.js: $(shell node --version)" || echo "⚠️  Node.js not installed"
	@command -v npm >/dev/null 2>&1 && echo "✅ npm: $(shell npm --version)" || echo "⚠️  npm not installed"
	@echo "🏥 Diagnostics complete!"

# ==================== Docker ====================
up: check-env ## Start all services in background
	@echo "🚀 Starting all services..."
	$(DOCKER) up -d
	@echo "✅ Services started!"

down: ## Stop and remove all containers
	@echo "🛑 Stopping all services..."
	$(DOCKER) down
	@echo "✅ Services stopped!"

stop: ## Stop containers without removing them
	@echo "⏸️  Stopping containers..."
	$(DOCKER) stop

start: ## Start existing stopped containers
	@echo "▶️  Starting containers..."
	$(DOCKER) start

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(DOCKER) restart

ps: status ## Show running containers (alias)
status: ## Show container status
	@echo "📦 Container Status:"
	$(DOCKER) ps -a

build: ## Build all images (with cache)
	@echo "🔨 Building images..."
	$(DOCKER) build --pull

rebuild: ## Rebuild and restart services (no cache)
	@echo "🔄 Rebuilding and restarting..."
	$(DOCKER) down
	$(DOCKER) build --pull --no-cache
	$(DOCKER) up -d
	@echo "✅ Services rebuilt and restarted!"

clean: ## Remove containers and volumes (keeps images)
	@echo "🧹 Cleaning up..."
	$(DOCKER) down -v

clean-all: ## Remove containers, volumes, and images
	@echo "🗑️  Deep cleaning..."
	$(DOCKER) down -v --rmi all
	@echo "✅ Clean complete!"

# ==================== Logs ====================
logs: logs-backend ## Show backend logs (default)

logs-all: ## Show all logs with follow
	$(DOCKER) logs --tail=200 -f

logs-backend: ## Show backend logs
	$(DOCKER) logs --tail=200 -f backend

logs-frontend: ## Show frontend logs
	$(DOCKER) logs --tail=200 -f frontend

logs-db: ## Show database logs
	$(DOCKER) logs --tail=200 -f db

# ==================== Local Development ====================
dev: dev-backend ## Run backend locally (default)

dev-backend: ## Run backend dev server (uvicorn reload)
	@echo "🚀 Starting backend dev server..."
	@if [ ! -d $(BACKEND_DIR)/venv ]; then \
		echo "⚠️  Virtual environment not found, creating..."; \
		cd $(BACKEND_DIR) && python3 -m venv venv; \
	fi
	cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend dev server (Vite)
	@echo "🎨 Starting frontend dev server..."
	cd $(FRONTEND_DIR) && npm run dev

# ==================== Testing ====================
test: test-backend ## Run backend tests (default)

test-backend: ## Run backend pytest with summary
	@echo "🧪 Running backend tests..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && pytest -v --tb=short; \
	else \
		echo "⚠️  Running tests in Docker..."; \
		$(DOCKER) exec backend pytest -v --tb=short; \
	fi

test-watch: ## Run backend tests in watch mode
	@echo "👀 Running tests in watch mode..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && ptw; \
	else \
		echo "❌ ptw (pytest-watch) not installed or venv not found"; \
	fi

test-coverage: ## Run backend tests with coverage report
	@echo "📊 Running tests with coverage..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && pytest --cov=app --cov-report=term --cov-report=html; \
		echo "📈 Coverage report: file://$(shell pwd)/$(BACKEND_DIR)/htmlcov/index.html"; \
	else \
		$(DOCKER) exec backend pytest --cov=app --cov-report=term; \
	fi

test-frontend: ## Run frontend unit tests
	@echo "🎨 Running frontend tests..."
	cd $(FRONTEND_DIR) && npm test

test-e2e: ## Run Playwright E2E tests
	@echo "🎭 Running E2E tests..."
	cd $(FRONTEND_DIR) && npx playwright test

test-all: test-backend test-frontend test-e2e ## Run all test suites

# ==================== Dependencies ====================
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	@echo "📦 Installing backend dependencies..."
	@if [ ! -d $(BACKEND_DIR)/venv ]; then \
		echo "🐍 Creating virtual environment..."; \
		cd $(BACKEND_DIR) && python3 -m venv venv; \
	fi
	cd $(BACKEND_DIR) && . venv/bin/activate && pip install --upgrade pip
	cd $(BACKEND_DIR) && . venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Backend dependencies installed!"

install-frontend: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "✅ Frontend dependencies installed!"

# ==================== Database ====================
db-init: check-env ## Initialize database (up + migrate)
	@echo "🗄️  Initializing database..."
	$(DOCKER) up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	make migrate
	@echo "✅ Database initialized!"

migrate: ## Run Alembic migrations
	@echo "🔄 Running database migrations..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && alembic upgrade head; \
	else \
		$(DOCKER) exec backend alembic upgrade head; \
	fi
	@echo "✅ Migrations complete!"

migrate-create: ## Create new migration (usage: make migrate-create msg="description")
	@if [ -z "$(msg)" ]; then \
		echo "❌ Error: Please provide a migration message with msg=\"your message\""; \
		exit 1; \
	fi
	@echo "📝 Creating migration: $(msg)"
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && alembic revision --autogenerate -m "$(msg)"; \
	else \
		$(DOCKER) exec backend alembic revision --autogenerate -m "$(msg)"; \
	fi

db-reset: ## ⚠️  Reset database (DROP ALL DATA!)
	@echo "⚠️  ⚠️  ⚠️  WARNING: This will DELETE ALL DATA!"
	@echo "Type 'YES' to confirm, or anything else to cancel:"
	@read -r confirm; \
	if [ "$$confirm" = "YES" ]; then \
		echo "🗑️  Resetting database..."; \
		$(DOCKER) down -v; \
		$(DOCKER) up -d db; \
		sleep 5; \
		make migrate; \
		echo "✅ Database reset complete!"; \
	else \
		echo "❌ Database reset cancelled."; \
	fi

db-shell: ## Connect to PostgreSQL shell
	$(DOCKER) exec -it db psql -U postgres -d accounting

backup: ## Backup database to timestamped file
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	filename="backups/accounting_db_$$timestamp.sql"; \
	echo "💾 Backing up database to $$filename..."; \
	$(DOCKER) exec db pg_dump -U postgres -d accounting > $$filename; \
	echo "✅ Backup complete: $$filename"

restore: ## Restore database from backup (usage: make restore file=backups/xxx.sql)
	@if [ -z "$(file)" ]; then \
		echo "❌ Error: Please provide a backup file with file=path/to/backup.sql"; \
		exit 1; \
	fi
	@if [ ! -f "$(file)" ]; then \
		echo "❌ Error: File not found: $(file)"; \
		exit 1; \
	fi
	@echo "⚠️  This will overwrite the database!"
	@echo "Type 'YES' to confirm:"
	@read -r confirm; \
	if [ "$$confirm" = "YES" ]; then \
		echo "🔄 Restoring database from $(file)..."; \
		$(DOCKER) exec -T db psql -U postgres -d accounting < $(file); \
		echo "✅ Database restored!"; \
	else \
		echo "❌ Restore cancelled."; \
	fi

# ==================== Code Quality ====================
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code (ruff)
	@echo "🔍 Linting backend..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && ruff check . --fix; \
	else \
		$(DOCKER) exec backend ruff check . --fix; \
	fi

lint-frontend: ## Lint frontend code (eslint)
	@echo "🔍 Linting frontend..."
	cd $(FRONTEND_DIR) && npx eslint . --ext .ts,.vue --fix

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code (ruff format)
	@echo "🎨 Formatting backend..."
	@if [ -d $(BACKEND_DIR)/venv ]; then \
		cd $(BACKEND_DIR) && . venv/bin/activate && ruff format .; \
	else \
		$(DOCKER) exec backend ruff format .; \
	fi

format-frontend: ## Format frontend code (prettier)
	@echo "🎨 Formatting frontend..."
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,vue,css,scss,html,json}"

# ==================== Quick Start ====================
init: check-env ## Initialize project (check env, install deps)
	@echo "🎉 Initializing Accounting AI project..."
	make install
	@echo ""
	@echo "✅ Project initialized!"
	@echo "💡 Next steps:"
	@echo "   - Review and configure .env file"
	@echo "   - Run 'make up' to start services"
	@echo "   - Or 'make setup' for full setup"

setup: init build up ## Full setup (init + build + up)
	@sleep 5
	make migrate
	@echo ""
	@echo "🎉 Setup Complete!"
	@echo "===================="
	@echo "🌐 Frontend: http://localhost:${FRONTEND_PORT:-53000}"
	@echo "🔧 Backend: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "💡 Useful commands:"
	@echo "   - make logs     - View logs"
	@echo "   - make test     - Run tests"
	@echo "   - make help     - See all commands"

# ==================== Deployment ====================
deploy: ## Deploy locally (alias for rebuild)
	make rebuild
	@echo "✅ Deployed locally!"

deploy-prod: ## Production deployment (placeholder)
	@echo "🚀 Production deployment placeholder"
	@echo "Add your production deployment steps here"
