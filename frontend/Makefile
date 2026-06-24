.PHONY: help install install-ci build dev-build watch unit-tests coverage lint lint-fix serve serve-network clean all

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	npm install

install-ci: ## Install dependencies (CI-optimized)
	npm ci

build: ## Build production version
	npm run build

dev-build: ## Build development version
	npm run dev-build

watch: ## Watch and rebuild on changes
	npm run watch

unit-tests: ## Run tests
	npm run test

coverage: ## Run tests with coverage
	npm run coverage

lint: ## Check code for linting errors
	npm run lint
	npm run prettier

lint-fix: ## Auto-fix linting errors
	npm run lint-fix
	npm run prettier-fix

serve: ## Run development server on localhost
	npm run serve:local

serve-prod: ## Run prod server on localhost
	npm run serve:prod

serve-network: ## Run development server on network
	npm run serve:network

clean: ## Clean build artifacts
	rm -rf dist

all: install lint unit-tests build ## Install, lint, test, and build
