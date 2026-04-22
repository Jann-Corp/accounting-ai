.PHONY: help dev test test-e2e lint build deploy rebuild logs logs-backend logs-frontend ps restart down clean

# Docker project name
PROJECT := accounting-ai

# Docker command wrapper (use `sg docker -c "docker compose ..."` in sandbox)
DOCKER := sg docker -c "docker compose -p $(PROJECT)"

# ==============================================================================
# Local Development (本地开发)
# ==============================================================================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $< | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: ## Run backend locally (development)
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

test: ## Run backend pytest
	cd backend && source venv/bin/activate && pytest -q

test-e2e: ## Run Playwright E2E tests
	cd frontend && npx playwright test

lint: ## Run linters (backend + frontend)
	cd backend && source venv/bin/activate && ruff check . && mypy .
	cd frontend && npm run lint

# ==============================================================================
# Production Deployment (生产环境部署 - Docker)
# ==============================================================================

build: ## Rebuild Docker images (no cache)
	$(DOCKER) build --pull --no-cache

rebuild: build ## Rebuild and restart all containers
	$(DOCKER) up -d --force-recreate

deploy: rebuild ## Full deployment: rebuild images + recreate containers
	@echo "Deployment complete for $(PROJECT)"

logs: ## Show all logs (follow mode)
	$(DOCKER) logs --tail=100 -f

logs-backend: ## Show backend logs only
	$(DOCKER) logs --tail=100 -f backend

logs-frontend: ## Show frontend logs only
	$(DOCKER) logs --tail=100 -f frontend

ps: ## Show running containers
	$(DOCKER) ps

restart: ## Restart all containers (no rebuild)
	$(DOCKER) restart

down: ## Stop all containers
	$(DOCKER) stop

clean: ## Remove containers, volumes, and images
	$(DOCKER) down -v --rmi all
	@echo "Cleanup complete for $(PROJECT)"
