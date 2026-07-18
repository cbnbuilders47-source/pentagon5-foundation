SHELL := /bin/bash
.SHELLFLAGS := -Eeuo pipefail -c
export PATH := /opt/homebrew/opt/node/bin:$(HOME)/.cargo/bin:$(HOME)/.local/bin:$(PATH)

.DEFAULT_GOAL := bootstrap

.PHONY: doctor bootstrap secrets-init contracts-check runtime-test database-up \
	database-migrate database-downgrade database-seed database-test quality \
	frontend-setup frontend-test desktop-build rust-test stack-config stack-up \
	stack-health stack-down backend-up backend-health verify acceptance

doctor:
	@./infrastructure/scripts/doctor.sh

bootstrap:
	@$(MAKE) doctor
	@uv sync --all-extras --locked
	@npm ci --prefix packages/api-client
	@npm ci --prefix apps/macos-desktop
	@cargo fetch --locked --manifest-path apps/macos-desktop/src-tauri/Cargo.toml
	@uv run pre-commit install
	@printf 'bootstrap: locked Milestone 3 dependencies and Git hooks are ready\n'

secrets-init:
	@./infrastructure/scripts/secrets-init.sh

contracts-check:
	@uv run pytest tests/contract

runtime-test:
	@uv run pytest tests/unit tests/contract tests/security

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
	@uv run pytest tests/unit tests/contract tests/security

frontend-setup:
	@npm ci --prefix packages/api-client
	@npm ci --prefix apps/macos-desktop

frontend-test: frontend-setup
	@npm run typecheck --prefix packages/api-client
	@npm test --prefix packages/api-client
	@npm run build --prefix packages/api-client
	@npm run typecheck --prefix apps/macos-desktop
	@npm test --prefix apps/macos-desktop

desktop-build: frontend-test
	@npm run build --prefix apps/macos-desktop

rust-test:
	@cargo fmt --manifest-path apps/macos-desktop/src-tauri/Cargo.toml --check
	@cargo clippy --locked --manifest-path apps/macos-desktop/src-tauri/Cargo.toml \
		--all-targets -- -D warnings
	@cargo test --locked --manifest-path apps/macos-desktop/src-tauri/Cargo.toml

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

stack-up: secrets-init database-migrate
	@docker compose up --detach --wait

stack-health:
	@./infrastructure/scripts/stack-health.sh

stack-down:
	@docker compose down --remove-orphans
	@printf 'stack-down: named volumes were preserved\n'

backend-up: stack-up

backend-health: stack-health

verify: doctor quality frontend-test desktop-build rust-test
	@bash -n infrastructure/scripts/doctor.sh infrastructure/scripts/secrets-init.sh \
		infrastructure/scripts/stack-health.sh
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard) --show-diff-on-failure
	@docker compose config --quiet
	@uv lock --check
	@printf 'verify: Milestone 3 contracts, runtimes, desktop, and configuration are valid\n'

acceptance: verify database-test stack-up stack-health
	@printf 'acceptance: Milestone 3 local acceptance checks passed\n'
