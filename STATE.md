# STATE.md — Synapse

> **Memória operacional do projeto.** Atualizado a cada bloco.
> Qualquer IA (principal ou auxiliar) que vá codar DEVE ler este arquivo primeiro,
> junto com `docs/PRD.md` e `docs/TECH_SPECS.md`.

**Produto:** Synapse — SRS para estudantes de alta performance
**Case:** 10 dias (24/04 – 04/05/2026)
**Última atualização:** 2026-04-24 — início do Dia 1

---

## 📍 Dia corrente: **Dia 1 — Fundação**

### Status: 🟡 em andamento

### Objetivo do dia
Subir infra (Postgres + Temporal + UI) e deixar o monorepo estruturado para receber os 3 clientes nos dias seguintes.

### Acceptance criteria
- `make up` sobe tudo; `make ps` mostra todos healthy
- http://localhost:8080 abre UI do Temporal
- `make psql` conecta no db `synapse`
- Repo commitado no GitHub

---

## ✅ Feito (cumulativo)
_(nada ainda — primeiro dia)_

## 🟡 Em andamento
- Setup inicial do monorepo

## ⬜ Pendente — Dia 1
- [ ] Estrutura de pastas e `.gitignore`
- [ ] `README.md` raiz
- [ ] `docs/PRD.md` e `docs/TECH_SPECS.md`
- [ ] `docker-compose.yml` + `infra/postgres/init-temporal-db.sh` + `infra/temporal/development.yaml`
- [ ] `.env.example` e `.env`
- [ ] `Makefile`
- [ ] Validar `make up` + Temporal UI
- [ ] Scaffolds `api/`, `worker/`, `web/`, `mobile/` com READMEs
- [ ] `.github/workflows/ci.yml` stub
- [ ] Primeiro push ao GitHub

## ⬜ Pendente — próximos dias
- Dia 2 (25/04): Django+Ninja skeleton, User model, JWT, CRUD Deck
- Dia 3 (26/04): Card CRUD, SM-2 + testes, SRSRecomputeWorkflow
- Dia 4 (27/04): OfflineSyncWorkflow, `/sync`, `/review/today`, `/stats/dashboard`
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
- **Workflows:** Temporal 1.24+ em Docker; worker em Python SDK
- **Web:** Next.js 14 (App Router) + Tailwind + shadcn/ui + TanStack Query; landing em `/`
- **Mobile:** Flutter 3.x + Drift + Dio + Riverpod
- **Monorepo:** `api/`, `worker/`, `web/`, `mobile/`, `infra/`, `docs/`
- **Auth:** JWT Bearer, mesmo padrão em web e mobile
- **SRS:** SM-2 no MVP, interface plugável (`SRSEngine.compute_next(card, rating)`)

## 🔑 Decisões fixadas
- Produto: **Synapse**
- Landing: Hero + 3 seções + CTA (enxuta)
- Offline: só create + review offline (update/delete apenas online)
- Sync: last-write-wins com flag; sem UI de merge

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
