COMPOSE ?= docker compose
MASTA_PORT ?= 8000
export MASTA_PORT

.DEFAULT_GOAL := help
.PHONY: help up down restart build logs ps shell

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.env:
	cp .env.example .env
	@echo "Created .env from .env.example - add a provider API key, then 'make restart'."

up: .env ## Build and start masta at http://localhost:8000 (MASTA_PORT to change)
	$(COMPOSE) up --build --detach
	@echo "masta is running at http://localhost:$(MASTA_PORT)"

down: ## Stop masta (your data is kept in the masta-data volume)
	$(COMPOSE) down

restart: .env ## Recreate the container, picking up changes to .env
	$(COMPOSE) up --detach --force-recreate

build: ## Build the image without starting it
	$(COMPOSE) build

logs: ## Follow the server logs
	$(COMPOSE) logs --follow

ps: ## Show container status
	$(COMPOSE) ps

shell: ## Open a shell in the running container (the masta CLI is on PATH)
	$(COMPOSE) exec masta bash
