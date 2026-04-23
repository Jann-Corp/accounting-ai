.PHONY: help up down restart ps logs logs-backend logs-frontend logs-db \
        build build-backend build-frontend rebuild rebuild-backend rebuild-frontend \
        deploy deploy-backend deploy-frontend \
        clean status

# ==================== Configuration ====================
DOCKER_COMPOSE := docker compose -p accounting-ai
COMPOSE_FILE := docker-compose.yml

# Default target
.DEFAULT_GOAL := help

# ==================== Help ====================
help: ## Show this help message
	@echo "📊 Accounting AI - Makefile Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Quick Start: make up"

# ==================== Docker ====================
up: ## Start all services
	@echo "🚀 Starting all services..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started!"

down: ## Stop and remove all containers
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Services stopped!"

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(DOCKER_COMPOSE) restart
	@echo "✅ Services restarted!"

ps: status ## Show all project containers (alias)
status: ## Show all project containers status
	@echo "📦 Container Status for project 'accounting-ai':"
	$(DOCKER_COMPOSE) ps -a

clean: ## Remove containers and volumes
	@echo "🧹 Cleaning up..."
	$(DOCKER_COMPOSE) down -v

# ==================== Build ====================
build: build-backend build-frontend ## Build all images (with cache)

build-backend: ## Build backend image only
	@echo "🔨 Building backend image..."
	$(DOCKER_COMPOSE) build backend

build-frontend: ## Build frontend image only
	@echo "🔨 Building frontend image..."
	$(DOCKER_COMPOSE) build frontend

rebuild: rebuild-backend rebuild-frontend ## Rebuild all images (no cache)

rebuild-backend: ## Rebuild backend image only (no cache)
	@echo "🔄 Rebuilding backend image (no cache)..."
	$(DOCKER_COMPOSE) build --no-cache backend

rebuild-frontend: ## Rebuild frontend image only (no cache)
	@echo "🔄 Rebuilding frontend image (no cache)..."
	$(DOCKER_COMPOSE) build --no-cache frontend

# ==================== Deploy (Build + Replace) ====================
deploy: deploy-backend deploy-frontend ## Build and deploy all services

deploy-backend: ## Build and deploy backend only (replace container)
	@echo "🚀 Building and deploying backend..."
	$(DOCKER_COMPOSE) up -d --build --force-recreate --no-deps backend
	@echo "✅ Backend deployed!"

deploy-frontend: ## Build and deploy frontend only (replace container)
	@echo "🚀 Building and deploying frontend..."
	$(DOCKER_COMPOSE) up -d --build --force-recreate --no-deps frontend
	@echo "✅ Frontend deployed!"

# ==================== Logs ====================
logs: logs-backend ## Show backend logs (default)

logs-backend: ## Show backend logs (follow)
	@echo "📋 Backend logs:"
	$(DOCKER_COMPOSE) logs --tail=200 -f backend

logs-frontend: ## Show frontend logs (follow)
	@echo "🎨 Frontend logs:"
	$(DOCKER_COMPOSE) logs --tail=200 -f frontend

logs-db: ## Show database logs (follow)
	@echo "🗄️  Database logs:"
	$(DOCKER_COMPOSE) logs --tail=200 -f db

logs-all: ## Show all logs (follow)
	@echo "📋 All logs:"
	$(DOCKER_COMPOSE) logs --tail=200 -f
