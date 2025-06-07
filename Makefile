# Schedium Backend - Makefile
# Development automation commands

.PHONY: help install install-dev clean test run migrate validate

# Variables
PYTHON := python
PIP := pip
UVICORN := uvicorn
ALEMBIC := alembic
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy

# Default target
help:
	@echo "📋 Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install all dependencies (including dev)"
	@echo "  make clean        - Remove cache files"
	@echo "  make test         - Run all tests"
	@echo "  make run          - Start development server"
	@echo "  make migrate      - Run database migrations"
	@echo "  make validate     - Run complete validation"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Run linting checks"
	@echo "  make security     - Check security vulnerabilities"

# Installation
install:
	@echo "📦 Installing production dependencies..."
	$(PIP) install -r requirements.txt

install-dev: install
	@echo "📦 Installing development dependencies..."
	$(PIP) install -r requirements-dev.txt

# Cleaning
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Development server
run:
	@echo "🚀 Starting development server..."
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	@echo "🚀 Starting production server..."
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Database
migrate:
	@echo "📊 Running database migrations..."
	$(ALEMBIC) upgrade head

migrate-create:
	@echo "📝 Creating new migration..."
	@read -p "Enter migration message: " msg; \
	$(ALEMBIC) revision --autogenerate -m "$$msg"

migrate-downgrade:
	@echo "⬇️  Downgrading database..."
	$(ALEMBIC) downgrade -1

db-reset:
	@echo "🔄 Resetting database..."
	$(ALEMBIC) downgrade base
	$(ALEMBIC) upgrade head

# Testing
test:
	@echo "🧪 Running tests..."
	$(PYTEST) -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	$(PYTEST) --cov=app --cov-report=html --cov-report=term-missing

test-unit:
	@echo "🧪 Running unit tests..."
	$(PYTEST) tests/unit -v

test-integration:
	@echo "🧪 Running integration tests..."
	$(PYTEST) tests/integration -v

# Code quality
format:
	@echo "🎨 Formatting code..."
	$(BLACK) .

lint:
	@echo "🔍 Running linting checks..."
	$(FLAKE8) app tests
	$(MYPY) app

# Security
security:
	@echo "🔒 Checking security vulnerabilities..."
	pip-audit
	bandit -r app/

# Validation
validate:
	@echo "✅ Running complete validation..."
	$(PYTHON) scripts/validate_installation.py

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t schedium-backend:latest .

docker-run:
	@echo "🐳 Running Docker container..."
	docker-compose up -d

docker-stop:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Database utilities
db-create-admin:
	@echo "👤 Creating admin user..."
	$(PYTHON) scripts/create_admin_user.py

db-seed:
	@echo "🌱 Seeding database..."
	$(PYTHON) scripts/seed_data.py

# Development setup
setup: install-dev
	@echo "🔧 Setting up development environment..."
	cp .env.example .env
	@echo "✅ Setup complete! Don't forget to:"
	@echo "   1. Edit .env with your database credentials"
	@echo "   2. Run 'make migrate' to setup database"
	@echo "   3. Run 'make db-create-admin' to create admin user"

# Quick commands
dev: clean format lint test run

check: format lint security test