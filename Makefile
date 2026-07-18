SHELL := /bin/bash
.SHELLFLAGS := -Eeuo pipefail -c
export PATH := /opt/homebrew/opt/node/bin:$(HOME)/.cargo/bin:$(HOME)/.local/bin:$(PATH)

.DEFAULT_GOAL := bootstrap

.PHONY: doctor bootstrap contracts-check database-up database-migrate \
	database-downgrade database-seed database-test quality stack-config \
	stack-up stack-health stack-down verify acceptance

doctor:
	@./infrastructure/scripts/doctor.sh

bootstrap:
	@$(MAKE) doctor
	@uv sync --all-extras --locked
	@uv run pre-commit install
	@printf 'bootstrap: locked Milestone 2 dependencies and Git hooks are ready\n'

contracts-check:
	@uv run pytest tests/contract

database-up:
	@docker compose up --detach --wait postgres

database-migrate: stack-config database-up
	@set -a; source .env; set +a; \
		DATABASE_URL="postgresql+psycopg://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@127.0.0.1:$${POSTGRES_PORT}/$${POSTGRES_DB}" \
		uv run alembic -c infrastructure/database/alembic.ini upgrade head

database-downgrade: stack-config database-up
	@set -a; source .env; set +a; \
		DATABASE_URL="postgresql+psycopg://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@127.0.0.1:$${POSTGRES_PORT}/$${POSTGRES_DB}" \
		uv run alembic -c infrastructure/database/alembic.ini downgrade base

database-seed: database-migrate
	@docker compose exec -T -e PGOPTIONS="-c app.environment=development" postgres psql \
		--username pentagon5 --dbname pentagon5 --set ON_ERROR_STOP=1 \
		< infrastructure/database/seed.development.sql

database-test: stack-config database-up
	@set -a; source .env; set +a; \
		TEST_DATABASE_URL="postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@127.0.0.1:$${POSTGRES_PORT}/postgres" \
		uv run pytest tests/integration

quality:
	@uv run ruff format --check .
	@uv run ruff check .
	@uv run mypy .
	@uv run pytest tests/contract

stack-config:
	@if [[ -e .env || -L .env ]]; then \
		printf 'stack-config: preserving existing .env\n'; \
	elif [[ -L .env.example ]]; then \
		printf 'stack-config: refusing symlinked .env.example\n' >&2; \
		exit 1; \
	elif [[ -f .env.example ]]; then \
		umask 077; \
		install -m 600 .env.example .env; \
		printf 'stack-config: created private .env from .env.example\n'; \
	else \
		printf 'stack-config: .env.example is absent; using development defaults from docker-compose.yml\n'; \
	fi

stack-up:
	@docker compose up --detach --wait

stack-health:
	@./infrastructure/scripts/stack-health.sh

stack-down:
	@docker compose down --remove-orphans
	@printf 'stack-down: named volumes were preserved\n'

verify: doctor quality
	@bash -n infrastructure/scripts/doctor.sh infrastructure/scripts/stack-health.sh
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard) --show-diff-on-failure
	@docker compose config --quiet
	@uv lock --check
	@printf 'verify: contracts, quality, and local infrastructure configuration are valid\n'

acceptance: verify database-test stack-up stack-health
	@printf 'acceptance: Milestone 2 local acceptance checks passed\n'
