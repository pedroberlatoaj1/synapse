# worker/ — Synapse Temporal Worker

Worker Python que hospeda os workflows e activities do Temporal.io.
Processa trabalho assíncrono e durável fora do caminho crítico da API.

## Workflows hospedados
| Workflow | Disparo | Workflow ID | Papel |
|---|---|---|---|
| `ReviewPersistenceWorkflow` | pós-commit de `POST /review` | `review-persist-{review.id}` | Log histórico + atualizar agregados (streak, retention) + analytics. **NÃO** roda SM-2 (isso é síncrono na API). |
| `OfflineSyncWorkflow` | `POST /sync` | `sync-event-{event.id}` | Aplica `SyncEvent` com LWW ordenado por `client_ts`, serialização por `(user_id, entity_id)` via `pg_advisory_xact_lock`. |
| `ReviewSchedulerWorkflow` *(se prazo permitir)* | cron por usuário (fuso local) | `scheduler-{user_id}-{date}` | Calcula cards devidos e dispara push/email. |
| `RetentionAnalyticsWorkflow` *(se prazo permitir)* | cron semanal | `retention-{week}` | Agrega métricas pesadas. |

**Scope mínimo:** se o prazo apertar, entregar apenas `ReviewPersistenceWorkflow` + `OfflineSyncWorkflow`.

## Invariantes de idempotência (obrigatórias)
- Todo workflow tem ID **determinístico** derivado de uma idempotency key do cliente.
- Activities que mutam Postgres devem ser idempotentes (ex.: `INSERT ... ON CONFLICT (id) DO NOTHING`).
- LWW: conflitos comparam `client_ts`; empate resolvido por `id` lexicograficamente maior.
- Serialização por entidade: `SELECT pg_advisory_xact_lock(hashtextextended(user_id::text || entity_id::text, 0))`.

## Stack
- Python 3.12
- `temporalio` SDK
- `psycopg` (cliente Postgres direto — worker não depende do Django ORM)
- Lint: `ruff`
- Testes: `pytest` + `pytest-asyncio`

## Layout (a ser criado no Dia 3)
```
worker/
├── pyproject.toml
├── worker/
│   ├── main.py                 # registra workflows + activities, conecta no Temporal
│   ├── workflows/
│   │   ├── review_persistence.py
│   │   └── offline_sync.py
│   ├── activities/
│   │   ├── db.py               # activities que tocam Postgres
│   │   └── analytics.py
│   └── srs/                    # SM-2 (mesmo módulo usado pela API)
└── tests/
```

## Dev
A partir do Dia 3:
```bash
make worker-install
make worker-run     # conecta em temporal:7233, task queue "synapse-default"
make worker-test
```

> Ver `docs/TECH_SPECS.md` §4 e §4.1 para contratos e invariantes.
