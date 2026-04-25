ROOT := $(abspath .)

ifeq ($(OS),Windows_NT)
	VENV_PY := $(ROOT)/api/.venv/Scripts/python.exe
else
	VENV_PY := $(ROOT)/api/.venv/bin/python
endif

.PHONY: help up down restart logs ps psql clean temporal-cli \
        api-install api-migrate api-run api-test api-shell

help:
	@echo "Synapse — comandos de desenvolvimento"
	@echo ""
	@echo "  Infra (docker compose):"
	@echo "    make up           - Sobe postgres + temporal + temporal-ui"
	@echo "    make down         - Derruba os serviços (mantém volumes)"
	@echo "    make restart      - down + up"
	@echo "    make logs         - Tail logs de todos os serviços"
	@echo "    make ps           - Status dos containers"
	@echo "    make psql         - Conecta no db 'synapse'"
	@echo "    make temporal-cli - Descreve o namespace default no Temporal"
	@echo "    make clean        - APAGA volumes (reset total)"
	@echo ""
	@echo "  API (Django):"
	@echo "    make api-install  - Cria api/.venv e instala deps (pip install -e .[dev])"
	@echo "    make api-migrate  - Aplica migrations no db 'synapse'"
	@echo "    make api-run      - Sobe runserver em http://localhost:8000"
	@echo "    make api-test     - Roda ruff + pytest"
	@echo "    make api-shell    - Abre shell Django (REPL com models)"

up:
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

psql:
	docker compose exec postgres psql -U synapse -d synapse

temporal-cli:
	docker compose exec temporal tctl --namespace default namespace describe

clean:
	docker compose down -v
	@echo "Volumes apagados."

# -----------------------------------------------------------------
# API (Django) — ativado a partir do Dia 2
# -----------------------------------------------------------------

api-install:
	@test -d api/.venv || python -m venv api/.venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -e "./api[dev]"

api-migrate:
	cd api && $(VENV_PY) manage.py migrate

api-run:
	cd api && $(VENV_PY) manage.py runserver 0.0.0.0:8000

api-test:
	cd api && $(VENV_PY) -m ruff check .
	cd api && $(VENV_PY) -m pytest

api-shell:
	cd api && $(VENV_PY) manage.py shell
