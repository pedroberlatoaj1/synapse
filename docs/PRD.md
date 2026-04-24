# PRD — Synapse

> Spaced Repetition System para estudantes de alta performance.
> Case de estágio — 10 dias (24/04–04/05/2026).

## 1. Pitch em uma linha
> **"Anki foi feito por hackers. Synapse é para atletas cognitivos."**
> Plataforma de repetição espaçada que usa princípios de neurociência (janelas de consolidação, carga cognitiva, cronobiologia) para maximizar retenção em estudantes de alta performance — vestibular, medicina, engenharia, concursos.

## 2. Proposta de valor (o que nos diferencia de Anki/Quizlet)
| Eixo | Anki/Quizlet | Synapse |
|---|---|---|
| Foco | generalista | alta performance em ciências exatas + concursos |
| SRS | SM-2 cru | SM-2 + ajuste cronobiológico (sessões sugeridas por janela cognitiva do usuário) |
| UX de estudo | clínica | micro-sessões (10–15min) com feedback neurocientífico (forgetting curve visual, retention index) |
| LaTeX/fórmulas | suporte via addon | nativo (prioridade de produto) |
| Mobile | app separado | **offline-first real** com sync durável |

## 3. Personas (MVP)
- **P1 — Pré-vestibulando de medicina (17–20):** revisa 200+ cards/dia; precisa de mobile sólido p/ estudar no transporte.
- **P2 — Universitário de exatas (19–24):** carga alta de fórmulas; quer LaTeX nativo e dashboard de progresso.
- **P3 — Concurseiro (25–40):** estuda em janelas longas; valoriza estatísticas de retenção por disciplina.

## 4. User Stories — MVP (escopo fechado em 10 dias)

**Core loop — obrigatório:**
- **US-01** Como usuário, me cadastro e faço login (email + senha, JWT).
- **US-02** Crio um deck com nome, descrição e tags.
- **US-03** Adiciono cards (frente/verso, suporte a LaTeX) em um deck.
- **US-04** Inicio uma sessão de revisão e avalio cada card em 4 níveis (Again / Hard / Good / Easy). O sistema reagenda o card via SRS.
- **US-05** Vejo um dashboard com: cards devidos hoje, streak, retention rate, heatmap.
- **US-06** No mobile, reviso cards **sem internet**; quando reconectar, sincroniza automaticamente.
- **US-07** Visitante anônimo acessa a landing page, entende o produto e converte para signup.

**Nice-to-have (só se sobrar tempo nos dias 9–10):**
- Compartilhar deck público via link.
- Push notification da sessão diária.
- "Focus mode": timer + bloqueio visual (angle de neurociência).

## 5. Non-goals (explícito — para proteger o prazo)
- ❌ Billing / planos pagos
- ❌ Colaboração em tempo real
- ❌ IA generativa para criar cards
- ❌ Gamificação social / ranking
- ❌ Multi-idioma (só PT-BR)
- ❌ Dark mode / theming
- ❌ Publicação na App Store / Play Store (demo via APK sideload)
- ❌ Import de Anki APKG
- ❌ Upload de imagem nos cards (só texto + LaTeX)
- ❌ Update/delete offline no mobile (só create + review offline; edits só online)

## 6. Métricas de sucesso do case
- API p95 < 200ms nos endpoints de review
- Cobertura de testes backend ≥ 60%
- Mobile abre em < 2s; sessão de review funciona 100% offline
- Demo end-to-end roda sem bugs no happy path
