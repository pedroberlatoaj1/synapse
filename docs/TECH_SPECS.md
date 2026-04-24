# Tech Specs — Synapse

## 1. Arquitetura em alto nível

```
        ┌────────────────┐       ┌────────────────┐
        │ Next.js SaaS   │       │ Flutter Mobile │
        │ + Landing      │       │ (offline-first)│
        └───────┬────────┘       └───────┬────────┘
                │ JWT / REST             │
                └──────────┬─────────────┘
                           ▼
                ┌──────────────────────┐
                │ Django + Ninja API   │
                │ (Gunicorn, Docker)   │
                └────┬─────────┬───────┘
                     │         │ signals/clients
                     ▼         ▼
              ┌──────────┐  ┌───────────────────┐
              │Postgres16│  │  Temporal Server  │
              └──────────┘  └─────────┬─────────┘
                                      ▼
                              ┌───────────────┐
                              │ Python Worker │
                              │ (workflows)   │
                              └───────────────┘
```

Monorepo simples: `api/` · `web/` · `mobile/` · `worker/` · `docker-compose.yml`.

## 2. Modelagem de dados (Postgres)

```text
User           (id uuid, email unique, password_hash, timezone, created_at)
Deck           (id uuid, user_id FK, name, description, tags[], is_public bool, timestamps)
Card           (id uuid, deck_id FK, front text, back text,
                ease_factor float=2.5, interval_days int=0, repetitions int=0,
                due_at timestamptz, state enum[new|learning|review|lapsed], timestamps)
Review         (id uuid, card_id FK, user_id FK, rating enum[again|hard|good|easy],
                prev_interval, new_interval, duration_ms, reviewed_at)
SyncEvent      (id uuid PK, user_id FK, device_id, entity_type, entity_id,
                op enum[create|update|review], payload jsonb,
                client_ts, server_ts, status enum[pending|applied|conflict])
-- NOTA: `id` é GERADO PELO CLIENTE (UUID v4/v7) e atua como idempotency key.
--       Servidor: INSERT ... ON CONFLICT (id) DO NOTHING.
--       Temporal: workflow_id = f"sync-event-{id}". Ver §4.1.
```

**Índices críticos:**
- `Card(deck_id, due_at)` — query da sessão diária
- `Review(user_id, reviewed_at DESC)` — heatmap e stats
- `Deck(user_id)` — listagem de decks do usuário (evita full scan em joins)
- `SyncEvent(user_id, device_id, server_ts)` — reconciliação por device em ordem cronológica
- `SyncEvent(user_id, status, server_ts)` — fila de eventos `pending`/`conflict` ordenada (substitui o índice simples `SyncEvent(user_id, status)`)

## 3. Algoritmo SRS
- **MVP:** SM-2 (Anki clássico) — ~100 linhas de Python, testado com unit tests.
- **Execução:** chamada **síncrona** dentro do `POST /review` (função pura, determinística, ~microssegundos). Responde o novo `due_at` ao cliente em <50ms. Nada de workflow Temporal no caminho crítico (ver §4.1).
- **Pós-MVP (non-goal):** FSRS. Deixar a interface do serviço SRS plugável (`SRSEngine.compute_next(card, rating) -> NewState`) para trocar sem reescrever endpoints.

## 4. Onde o Temporal entra (justificando arquiteturalmente)

| Workflow | Disparo | Por que Temporal (vs. síncrono / Celery) |
|---|---|---|
| **ReviewPersistenceWorkflow** | POST /review (pós SM-2 síncrono + commit) | **NÃO roda SM-2** (isso é síncrono na API, §3). Grava log histórico em `Review`, atualiza agregados (streak, retention) e dispara analytics. Workflow ID = `review-persist-{review.id}` (idempotente). Durabilidade garante que o log nunca se perde mesmo se o worker cair. |
| **OfflineSyncWorkflow** | POST /sync (batch do Flutter) | **Workflow ID = `sync-event-{event.id}`** (idempotência cross-retry — §4.1). LWW por `client_ts`; serialização por `(user_id, entity_id)` via `pg_advisory_xact_lock`; retries automáticos; conflitos viram tarefa explícita e observável. |
| **ReviewSchedulerWorkflow** | cron por usuário (1×/dia, fuso dele) | Calcula cards devidos e dispara push/email; tolera falhas sem perder dias |
| **RetentionAnalyticsWorkflow** | cron semanal | Agrega métricas pesadas; se demorar, não trava a API |

**Se o prazo apertar:** manter só `ReviewPersistenceWorkflow` + `OfflineSyncWorkflow`. Esses dois já justificam o Temporal no demo.

### 4.1 Idempotência & concorrência (regras de implementação)

Contratos obrigatórios para qualquer código que toque `/sync`, `/review` ou um workflow:

- **Idempotency key:** o cliente gera `SyncEvent.id` (UUID v4/v7). O servidor grava com `INSERT ... ON CONFLICT (id) DO NOTHING` e reutiliza o mesmo valor como **Workflow ID do Temporal** (`workflow_id = f"sync-event-{id}"`). Retries HTTP do `/sync` NUNCA executam um workflow em duplicata.
- **LWW ordenado:** conflitos em `SyncEvent` sobre a mesma `entity_id` são resolvidos comparando `client_ts` (não `server_ts`) — o cliente é a fonte de verdade temporal para ações offline. Empate determinístico: vence o evento com `id` lexicograficamente maior.
- **Serialização por entidade:** antes de aplicar um evento, adquirir lock advisory transacional com `SELECT pg_advisory_xact_lock(hashtextextended(user_id::text || entity_id::text, 0))`. Serializa a fila por `(user_id, entity_id)` e elimina race entre múltiplos devices do mesmo usuário.
- **Review crítico:** `POST /review` faz `INSERT INTO review` + `UPDATE card (ease_factor, interval_days, due_at, …)` em **uma única transação síncrona**. Só **depois do commit** o worker dispara `ReviewPersistenceWorkflow` para analytics/agregados. Workflow ID = `review-persist-{review.id}` (idempotente).

## 5. Stack detalhada
| Camada | Escolha | Motivo |
|---|---|---|
| API | Django 5 + Ninja 1.x + `django-ninja-jwt` | Pedido do case; Ninja dá type hints e OpenAPI grátis |
| DB | Postgres 16 | Pedido do case |
| Workflows | Temporal.io (local via Docker) | Bônus arquitetural pedido |
| Worker | Python SDK do Temporal | Mesma linguagem do backend |
| Web | Next.js 14 (App Router) + Tailwind + shadcn/ui + TanStack Query | SEO na landing + SPA no app; shadcn acelera UI |
| Mobile | Flutter 3.x + Drift (SQLite) + Dio + Riverpod | Drift tipa migrations; Riverpod é mais limpo que Provider/BLoC puro |
| Landing | Rota `/` do Next.js com SSG | Um projeto a menos para deployar |
| Dev infra | docker-compose (postgres + temporal + api + worker) | Subir o stack com 1 comando |
| Deploy demo | Railway/Fly (api+worker+temporal), Vercel (web), APK direto (mobile) | Zero config; free tier aguenta demo |

## 6. Contratos de API (esqueleto)

```
POST   /auth/register          → {access, refresh}
POST   /auth/login             → {access, refresh}
POST   /auth/refresh           → {access}

GET    /decks
POST   /decks
PATCH  /decks/{id}
DELETE /decks/{id}

GET    /decks/{id}/cards
POST   /decks/{id}/cards
PATCH  /cards/{id}
DELETE /cards/{id}

GET    /review/today           → {cards: [...], due_count}
POST   /review                 → {next_due_at}      # SM-2 SÍNCRONO (<50ms, 1 txn)
                                                    # pós-commit: enqueue ReviewPersistenceWorkflow
                                                    # (log histórico + analytics, não-bloqueante)

POST   /sync                   → {accepted, conflicts, snapshot}
                                                    # enqueue OfflineSyncWorkflow

GET    /stats/dashboard        → {streak, retention_rate, heatmap, due_tomorrow}
```

## 7. Cronograma macro — 10 dias (24/04 → 04/05/2026)

| # | Data | Foco do dia | Entregável verificável |
|---|---|---|---|
| 1 | **Qui 24/04** | Fundação | Repo, docker-compose (postgres+temporal), PRD+Specs no README |
| 2 | **Sex 25/04** | Backend core | User+JWT, CRUD Deck, testes, OpenAPI em `/api/docs` |
| 3 | **Sáb 26/04** | SRS engine | CRUD Card, SM-2 com testes, `POST /review` + `ReviewPersistenceWorkflow` |
| 4 | **Dom 27/04** | Sync backend + **gate contratual** | `POST /sync` + `OfflineSyncWorkflow`, `/review/today`, `/stats/dashboard`; **suíte Insomnia/Postman exercendo payloads canônicos de `/sync` e `/review` ponta-a-ponta (gate: se falhar, NÃO avança ao Dia 5)** |
| 5 | **Seg 28/04** | Web MVP | Next.js + auth, listagem/CRUD de decks, sessão de revisão funcional |
| 6 | **Ter 29/04** | Web polish | Dashboard com heatmap, LaTeX rendering, skeleton states |
| 7 | **Qua 30/04** | Mobile base | Flutter bootstrap, Drift schema, auth + listagem de decks |
| 8 | **Qui 01/05** *(feriado)* | Mobile offline | Sessão offline + sync via `/sync`, teste airplane mode |
| 9 | **Sex 02/05** | Landing + polish | Landing page SEO, copy, polish geral, seed demo |
| 10 | **Sáb 03/05** | Ship | Deploy, vídeo 3min, README final, smoke E2E |
| buffer | **Dom 04/05** | Contingência | Bugs, retoques, enviar |

**Deadline-critical:** Dias 3, 4 e 8. Se algum atrasar → cortar landing elaborada e voltar ao core.

## 8. Decisões para **evitar overengineering**
- Sem Redis (Postgres aguenta o MVP).
- Sem S3/upload de mídia (non-goal).
- Sem microsserviços — tudo num único projeto Django.
- CI mínimo: um GitHub Actions rodando `pytest` + `ruff` no backend.
- Sem Kubernetes; deploy em PaaS.
- Dark mode, i18n, push notification — todos fora.

## 9. Riscos principais
| Risco | Prob | Mitigação |
|---|---|---|
| Sync offline do Flutter explodir em edge cases | **alta** | Escopo apertado: só create + review offline; update/delete só online |
| LaTeX no Flutter (`flutter_math_fork`) falhar em fórmulas complexas | média | Fallback: renderizar server-side para PNG em background |
| Temporal ser demorado pra configurar | média | Subir no **Dia 1** via docker-compose e validar um workflow hello-world antes do Dia 3 |
| Integração JWT entre web + mobile divergir | média | Padronizar client HTTP em ambos (access+refresh, interceptors), testar ponta-a-ponta no Dia 5 |
| Contrato de `/sync` ou `/review` quebrar só ao integrar mobile (Dia 8) | **alta** | Suíte Insomnia/Postman antecipada para **Dia 4** validando payloads canônicos; avanço ao Dia 5 bloqueado se falhar |
