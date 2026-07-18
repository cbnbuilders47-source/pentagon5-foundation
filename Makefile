SHELL := /bin/bash
.SHELLFLAGS := -Eeuo pipefail -c
export PATH := /opt/homebrew/opt/node/bin:$(HOME)/.cargo/bin:$(HOME)/.local/bin:$(PATH)

.DEFAULT_GOAL := bootstrap

.PHONY: doctor bootstrap stack-config stack-up stack-health stack-down verify

doctor:
	@./infrastructure/scripts/doctor.sh

bootstrap:
	@$(MAKE) doctor
	@uv sync --extra quality
	@uv run pre-commit install
	@printf 'bootstrap: Python quality environment and Git hooks are ready\n'

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

verify: doctor
	@bash -n infrastructure/scripts/doctor.sh infrastructure/scripts/stack-health.sh
	@uv run pre-commit run --files $$(git ls-files --cached --others --exclude-standard) --show-diff-on-failure
	@docker compose config --quiet
	@printf 'verify: local infrastructure configuration is valid\n'
