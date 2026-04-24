# Synapse

> Spaced Repetition System para estudantes de alta performance.
> Case de estágio em Engenharia de Software — 10 dias (24/04–04/05/2026).

## Stack
- **Backend:** Django 5 + Django Ninja + PostgreSQL 16
- **Workflows:** Temporal.io
- **Web:** Next.js 14 (App Router) + Tailwind + shadcn/ui
- **Mobile:** Flutter 3.x (offline-first) + Drift + Riverpod
- **Landing:** Next.js (rota `/`, SSG + SEO)

## Quick start (dev)
```bash
cp .env.example .env
make up          # sobe postgres + temporal + ui
make ps          # confirma healthy
```
- API:           http://localhost:8000 *(a partir do Dia 2)*
- Web:           http://localhost:3000 *(a partir do Dia 5)*
- Temporal UI:   http://localhost:8080

## Estrutura
- `api/`      — Django + Ninja (auth, CRUD, endpoints)
- `worker/`   — Temporal worker (SRS, sync)
- `web/`      — Next.js (SaaS + landing)
- `mobile/`   — Flutter (offline-first)
- `infra/`    — scripts e config de Postgres/Temporal
- `docs/`     — PRD e Tech Specs
- `STATE.md`  — estado operacional atual (sempre ler antes de codar)

## Docs
- [PRD](docs/PRD.md)
- [Tech Specs](docs/TECH_SPECS.md)
- [STATE](STATE.md)
