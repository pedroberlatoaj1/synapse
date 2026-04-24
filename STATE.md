# STATE.md — Synapse

> **Memória operacional do projeto.** Atualizado a cada bloco.
> Qualquer IA (principal ou auxiliar) que vá codar DEVE ler este arquivo primeiro,
> junto com `docs/PRD.md` e `docs/TECH_SPECS.md`.

**Produto:** Synapse — SRS para estudantes de alta performance
**Case:** 10 dias (24/04 – 04/05/2026)
**Última atualização:** 2026-04-24 — Dia 1 (Fundação) **100% concluído e auditado**. Monorepo estruturado, infra validada (`docker compose up -d` passa, Temporal UI em `localhost:8080`, dbs `synapse`/`temporal`/`temporal_visibility` criados), READMEs dos subprojetos populados, CI stub no lugar, repo publicado em `github.com/pedroberlatoaj1/synapse`. Resquício final corrigido: `SRSRecomputeWorkflow` → `ReviewPersistenceWorkflow` em `docs/TECH_SPECS.md` e neste STATE. Standby para Dia 2 (Backend Core) em 2026-04-25.

---

## 📍 Dia corrente: **Dia 1 — Fundação**

### Status: ✅ concluído

### Objetivo do dia
Subir infra (Postgres + Temporal + UI) e deixar o monorepo estruturado para receber os 3 clientes nos dias seguintes.

### Acceptance criteria
- [x] `make up` sobe tudo; `make ps` mostra todos healthy
- [x] http://localhost:8080 abre UI do Temporal (namespace `default` ativo)
- [x] `make psql` conecta no db `synapse`
- [x] Repo commitado no GitHub — `github.com/pedroberlatoaj1/synapse`, `main` tracking `origin/main`

---

## ✅ Feito (cumulativo)

### Dia 1 — 2026-04-24
- [x] Estrutura de pastas do monorepo e `.gitignore` — `95b3053`
- [x] `README.md` raiz — `95b3053`
- [x] `docs/PRD.md` e `docs/TECH_SPECS.md` — `2ee7d6e`
- [x] Patch arquitetural pós-auditoria (idempotência via Workflow ID, índices `SyncEvent`/`Deck`, `/review` síncrono + `ReviewPersistenceWorkflow` async, LWW por `client_ts`, gate contratual Dia 4) — `0066d8a`
- [x] `docker-compose.yml` + `infra/postgres/init-temporal-db.sh` + `infra/temporal/development.yaml` — `028eb64`
- [x] `.env.example` e `.env` — `028eb64`
- [x] `Makefile` (`up`, `down`, `ps`, `logs`, `psql`, ...) — `028eb64`
- [x] **Validado `make up` + Temporal UI** (`localhost:8080`) e Postgres multi-db
- [x] Scaffolds `api/`, `worker/`, `web/`, `mobile/` com READMEs detalhados (responsabilidades, stack, layout planejado) — `e1fd047`
- [x] `.github/workflows/ci.yml` stub (jobs api/worker/web gated pelo manifest de cada subprojeto; passam até scaffold existir) — `f1ce55f`
- [x] Primeiro push ao GitHub — `github.com/pedroberlatoaj1/synapse`, 7 commits em `main`

## 🟡 Em andamento
_(nada — Dia 1 fechado, pronto para iniciar Dia 2 em 2026-04-25)_

## ⬜ Pendente — Dia 1
_(nenhum — todos os itens concluídos)_

## ⬜ Pendente — próximos dias
- Dia 2 (25/04): Django+Ninja skeleton, User model, JWT, CRUD Deck
- Dia 3 (26/04): Card CRUD, SM-2 + testes, ReviewPersistenceWorkflow
- Dia 4 (27/04): OfflineSyncWorkflow, `/sync`, `/review/today`, `/stats/dashboard`, **suíte Insomnia/Postman validando `/sync` e `/review` (gate para Dia 5)**
- Dia 5 (28/04): Next.js + auth + deck UI
- Dia 6 (29/04): Sessão de revisão web + dashboard + LaTeX
- Dia 7 (30/04): Flutter bootstrap + auth + lista decks
- Dia 8 (01/05): Sessão offline mobile + sync
- Dia 9 (02/05): Landing page + polish
- Dia 10 (03/05): Deploy + vídeo + smoke E2E
- Buffer (04/05): contingência

---

## 🏗 Arquitetura acordada (não mudar sem Tech Lead)
- **Backend:** Django 5 + Django Ninja 1.x + Gunicorn + `django-ninja-jwt`
- **DB:** Postgres 16 compartilhado — dbs separados: `synapse` (app), `temporal`, `temporal_visibility`
- **Workflows:** Temporal 1.24+ em Docker; worker em Python SDK. **Workflow IDs derivados de idempotency keys do cliente** para resistir a retries sem duplicação
- **Web:** Next.js 14 (App Router) + Tailwind + shadcn/ui + TanStack Query; landing em `/`
- **Mobile:** Flutter 3.x + Drift + Dio + Riverpod
- **Monorepo:** `api/`, `worker/`, `web/`, `mobile/`, `infra/`, `docs/`
- **Auth:** JWT Bearer, mesmo padrão em web e mobile
- **SRS:** SM-2 no MVP, interface plugável (`SRSEngine.compute_next(card, rating)`). **Execução síncrona em `POST /review` (<50ms)**; `ReviewPersistenceWorkflow` assíncrono só para log histórico + analytics (nunca no caminho crítico)

## 🔑 Decisões fixadas
- Produto: **Synapse**
- Landing: Hero + 3 seções + CTA (enxuta)
- Offline: só create + review offline (update/delete apenas online)
- **Sync — LWW ordenado:** conflitos resolvidos por `client_ts` (empate: `id` lexicográfico maior); serialização por `(user_id, entity_id)` via `pg_advisory_xact_lock`; sem UI de merge
- **Idempotência:** `SyncEvent.id` é gerado pelo cliente (UUID v4/v7) e atua como idempotency key; servidor faz `INSERT ... ON CONFLICT (id) DO NOTHING`; Temporal `workflow_id = f"sync-event-{id}"`
- **Contrato `/review`:** SM-2 roda SÍNCRONO dentro da request (<50ms); `ReviewPersistenceWorkflow` é disparado APÓS o commit para log/analytics (`workflow_id = review-persist-{review.id}`)
- **Gate de validação contratual:** antes de avançar do Dia 4 para o Dia 5, suíte Insomnia/Postman tem que passar em `/sync` e `/review`

## 📦 Endpoints alvo (ver `docs/TECH_SPECS.md` §6 para contrato completo)
`/auth/register` `/auth/login` `/auth/refresh`
`/decks` (CRUD) `/decks/{id}/cards` `/cards/{id}`
`/review/today` `/review`
`/sync`
`/stats/dashboard`

## ⚠️ Issues / riscos abertos
_(nenhum no momento)_

---

## 🤖 Handover para IA auxiliar
Se você está assumindo este projeto no meio do trabalho:
1. Leia este arquivo inteiro, depois `docs/PRD.md` e `docs/TECH_SPECS.md`.
2. Pegue a próxima tarefa em **⬜ Pendente — Dia corrente**.
3. Siga os padrões em **🏗 Arquitetura acordada** — NÃO improvise stack.
4. Ao terminar uma tarefa:
   - Mova-a para ✅ com a data.
   - Atualize `Última atualização` no topo.
   - Commit descritivo (`feat:`, `fix:`, `chore:`, `docs:`).
5. Não mude itens em **🔑 Decisões fixadas** sem consultar o Tech Lead humano (Pedro).
6. Se ficar bloqueado, documente o bloqueio em **⚠️ Issues / riscos** e pare — não invente.
