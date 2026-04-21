.PHONY: help up down build logs logs-backend restart test test-e2e ps clean dev

# Docker commands (use `sg docker -c "docker compose ..."` in sandbox)
DOCKER := sg docker -c "docker compose"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $< | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	$(DOCKER) up -d

down: ## Stop all services
	$(DOCKER) down

build: ## Rebuild images
	$(DOCKER) build --pull

restart: ## Restart all services
	$(DOCKER) restart

logs: ## Show all logs
	$(DOCKER) logs --tail=100 -f

logs-backend: ## Show backend logs
	$(DOCKER) logs --tail=100 -f backend

ps: ## Show running containers
	$(DOCKER) ps

clean: ## Remove containers, volumes, and images
	$(DOCKER) down -v --rmi all

test: ## Run backend pytest
	cd backend && source venv/bin/activate && pytest -q

test-e2e: ## Run Playwright E2E tests
	cd frontend && npx playwright test

dev: ## Run backend locally (development)
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
