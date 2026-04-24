# api/ — Synapse Backend

Django 5 + Django Ninja 1.x + PostgreSQL 16.
Responsável por auth (JWT), CRUD de decks/cards, endpoints de review/sync/stats e cliente Temporal.

## Responsabilidades
- Autenticação JWT (`django-ninja-jwt`)
- CRUD de `Deck`, `Card`, `Review`
- `POST /review` — executa SM-2 **síncrono** (<50ms, 1 transação) e dispara `ReviewPersistenceWorkflow` pós-commit
- `POST /sync` — grava `SyncEvent` (idempotent via client UUID) e dispara `OfflineSyncWorkflow`
- `GET /review/today` e `GET /stats/dashboard`
- OpenAPI automático em `/api/docs`

## Stack
- Django 5, Django Ninja 1.x, `django-ninja-jwt`
- Postgres 16 (db `synapse`)
- `temporalio` SDK (cliente para o worker)
- Gunicorn em produção
- Testes: `pytest` + `pytest-django`
- Lint: `ruff`

## Layout (a ser criado no Dia 2)
```
api/
├── manage.py
├── pyproject.toml
├── synapse/            # Django project (settings, urls, wsgi)
├── apps/
│   ├── accounts/       # User, auth endpoints
│   ├── decks/          # Deck + Card models + endpoints
│   ├── reviews/        # Review model, SM-2 engine, /review endpoints
│   └── sync/           # SyncEvent, /sync endpoint
└── tests/
```

## Dev
A partir do Dia 2:
```bash
make api-install
make api-migrate
make api-run         # http://localhost:8000
make api-test
```

> Ver `docs/TECH_SPECS.md` §2, §3, §4.1 e §6 para contratos e invariantes.
