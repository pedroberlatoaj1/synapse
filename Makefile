.PHONY: help up down restart logs ps psql clean temporal-cli

help:
	@echo "Synapse — comandos de desenvolvimento"
	@echo "  make up           - Sobe postgres + temporal + temporal-ui"
	@echo "  make down         - Derruba os serviços (mantém volumes)"
	@echo "  make restart      - down + up"
	@echo "  make logs         - Tail logs de todos os serviços"
	@echo "  make ps           - Status dos containers"
	@echo "  make psql         - Conecta no db 'synapse'"
	@echo "  make temporal-cli - Descreve o namespace default no Temporal"
	@echo "  make clean        - APAGA volumes (reset total)"

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
