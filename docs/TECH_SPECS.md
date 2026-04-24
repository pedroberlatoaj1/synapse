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
SyncEvent      (id uuid, user_id FK, device_id, entity_type, entity_id,
                op enum[create|update|review], payload jsonb,
                client_ts, server_ts, status enum[pending|applied|conflict])
```

**Índices críticos:**
- `Card(deck_id, due_at)` — query da sessão diária
- `Review(user_id, reviewed_at DESC)` — heatmap e stats
- `SyncEvent(user_id, status)` — fila de reconciliação

## 3. Algoritmo SRS
- **MVP:** SM-2 (Anki clássico) — ~100 linhas de Python, testado com unit tests.
- **Pós-MVP (non-goal):** FSRS. Deixar a interface do serviço SRS plugável (`SRSEngine.compute_next(card, rating) -> NewState`) para trocar sem reescrever endpoints.

## 4. Onde o Temporal entra (justificando arquiteturalmente)

| Workflow | Disparo | Por que Temporal (vs. síncrono / Celery) |
|---|---|---|
| **SRSRecomputeWorkflow** | POST /review | Desacopla o request mobile (<50ms de resposta) do cálculo+persistência; durabilidade garante que nenhum review se perde se o worker cair |
| **OfflineSyncWorkflow** | POST /sync (batch do Flutter) | Reconciliação com retries automáticos; cada evento tem ciclo de vida observável; conflitos viram tarefa explícita |
| **ReviewSchedulerWorkflow** | cron por usuário (1×/dia, fuso dele) | Calcula cards devidos e dispara push/email; tolera falhas sem perder dias |
| **RetentionAnalyticsWorkflow** | cron semanal | Agrega métricas pesadas; se demorar, não trava a API |

**Se o prazo apertar:** manter só `SRSRecomputeWorkflow` + `OfflineSyncWorkflow`. Esses dois já justificam o Temporal no demo.

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
POST   /review                 → {next_due_at}      # enqueue SRSRecomputeWorkflow

POST   /sync                   → {accepted, conflicts, snapshot}
                                                    # enqueue OfflineSyncWorkflow

GET    /stats/dashboard        → {streak, retention_rate, heatmap, due_tomorrow}
```

## 7. Cronograma macro — 10 dias (24/04 → 04/05/2026)

| # | Data | Foco do dia | Entregável verificável |
|---|---|---|---|
| 1 | **Qui 24/04** | Fundação | Repo, docker-compose (postgres+temporal), PRD+Specs no README |
| 2 | **Sex 25/04** | Backend core | User+JWT, CRUD Deck, testes, OpenAPI em `/api/docs` |
| 3 | **Sáb 26/04** | SRS engine | CRUD Card, SM-2 com testes, `POST /review` + `SRSRecomputeWorkflow` |
| 4 | **Dom 27/04** | Sync backend | `POST /sync` + `OfflineSyncWorkflow`, `/review/today`, `/stats/dashboard` |
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
