# web/ — Synapse Web (SaaS + Landing)

Next.js 14 (App Router) hospedando tanto o **SaaS autenticado** quanto a **landing page** de marketing.

## Responsabilidades
- **Landing** (`/`) — SSG, SEO otimizado, CTA para cadastro.
- **Auth** (`/login`, `/register`) — fluxo JWT contra a API (access + refresh, interceptors).
- **App** (`/app/*`) — autenticado:
  - Listagem e CRUD de decks
  - Sessão de revisão com SM-2 (consome `POST /review`)
  - Dashboard: heatmap, streak, retention rate
  - Renderização LaTeX em fronts/backs de cards

## Stack
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS + `shadcn/ui`
- TanStack Query (data fetching + cache)
- `zod` para validação de forms
- KaTeX / `react-katex` para LaTeX
- Lint: ESLint + Prettier

## Layout (a ser criado no Dia 5)
```
web/
├── package.json
├── next.config.ts
├── src/
│   ├── app/
│   │   ├── (marketing)/        # landing SSG
│   │   ├── (auth)/             # login, register
│   │   └── (app)/              # app autenticado
│   ├── components/ui/          # shadcn
│   ├── lib/api.ts              # client HTTP com interceptors de JWT
│   └── features/
│       ├── decks/
│       ├── review/
│       └── stats/
└── tests/
```

## Dev
A partir do Dia 5:
```bash
cd web
pnpm install
pnpm dev             # http://localhost:3000
```

## Decisões fixadas
- Landing = rota `/` do mesmo projeto Next.js (um deploy a menos).
- Landing é **enxuta**: Hero + 3 seções + CTA (proteger prazo).
- Dark mode, i18n → **fora do MVP**.

> Ver `docs/TECH_SPECS.md` §5 e §6.
