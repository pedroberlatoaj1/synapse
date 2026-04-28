# STATE.md — Synapse

> **Memória operacional do projeto.** Atualizado a cada bloco.
> Qualquer IA (principal ou auxiliar) que vá codar DEVE ler este arquivo primeiro,
> junto com `docs/PRD.md` e `docs/TECH_SPECS.md`.

**Produto:** Synapse — SRS para estudantes de alta performance
**Case:** 10 dias (24/04 – 04/05/2026)
**Última atualização:** 2026-04-28 — Bloco 23 concluído e Dia 7 fechado: auth JWT auditada de ponta a ponta e riscos documentados para o MVP.

---

## 📍 Dia corrente: **Dia 8 — Polimento de UI/UX**

### Status: 🟡 Dia 8 em andamento

### Objetivo do dia
Polir a experiência Mobile/Web com ajustes visuais, filtros, estados de loading/empty/error e animações leves sem comprometer o fluxo offline-first.

---

## ✅ Feito (cumulativo)

### Dia 1 a Dia 3 — 2026-04-24 a 2026-04-26
- [x] Estrutura de pastas do monorepo, Docker, Postgres e READMEs raiz.
- [x] Setup Django 5.2 + Ninja API + JWT Customizado (AsyncJWTAuth).
- [x] CRUD completo e isolado multitenant para Decks e Cards.
- [x] Motor SM-2 isolado da infraestrutura (funções puras) e testado.
- [x] Endpoint Síncrono `POST /reviews` com validação de transação.

### Dia 4 — 2026-04-27 (Sync Foundation & Offline-First)
- [x] **Bloco 9 (Idempotência de Review):** `POST /reviews` blindado com `client_event_id` e *raw SQL* (`INSERT ... ON CONFLICT DO NOTHING`). Payload de resposta em cache para retries de rede.
- [x] **Bloco 10 (Pull Sync):** `GET /sync/changes`. Implementada paginação com Cursor Opaco Base64 (`updated_at` + `id`). Migração para *soft deletes* (`deleted_at`) em cascata e desnormalização de `user` no `Card` para otimizar index scan.
- [x] **Bloco 11 (Push Sync & LWW):** `POST /sync`. Ingestão em lote processando evento a evento em transações curtas. Resolução Last-Writer-Wins comparando `client_ts` com validação de fuso horário obrigatória. Isolamento de concorrência com `pg_advisory_xact_lock`. Máquina de estado para replays de rede e `savepoints` para erros de integridade.

### Dia 5 — 2026-04-27 (Mobile Foundation)
- [x] **Bloco 12 (Contrato Mobile-Sync & Fixtures):** Criado `mobile/docs/SYNC_CONTRACT.md` com ciclo oficial Initial Pull → Offline Work → Push Pending → Incremental Pull, política Server Wins sem merge UI no MVP, exemplos canônicos de `GET /sync/changes` e `POST /sync`, e `mobile/docs/sm2_fixtures.json` com 5 cenários derivados de `api/apps/reviews/sm2.py` para futura paridade Dart.
- [x] **Bloco 13 (Bootstrap Flutter):** Inicializada a fundação do app em `mobile/` com `pubspec.yaml`, dependências `flutter_riverpod`, `drift`, `sqlite3_flutter_libs`, `dio`, `uuid`, `flutter_secure_storage` e `connectivity_plus`, estrutura `lib/core/{api,db,srs}` + `lib/features/{auth,decks,review,sync}`, `main.dart` mínimo com Riverpod e `core/api/api_client.dart` com interceptor Bearer Token para Dio.
- [x] **Bloco 14 (Banco Local Drift):** Criado schema local em `mobile/lib/core/db/tables.dart` para `LocalDecks`, `LocalCards` e `SyncEvents`, com fila persistente `queued/sending/accepted/conflict`, checks de domínio e `UtcDateTimeConverter` que rejeita DateTime não-UTC. Criado `mobile/lib/core/db/database.dart` com `AppDatabase`, conexão SQLite local, PRAGMA de integridade/WAL e DAOs básicos para upsert/leitura de decks/cards e manipulação da fila de sync.
- [x] **Bloco 15 - SM-2 Local e Paridade:** Implementado `mobile/lib/core/srs/sm2.dart` com a mesma lógica pura do backend Python (`api/apps/reviews/sm2.py`), incluindo limites de ease/intervalo e arredondamento half-to-even. Criado `mobile/test/core/srs/sm2_test.dart` para varrer `mobile/docs/sm2_fixtures.json` e validar paridade absoluta dos outputs.
- [x] **Bloco 16 - Motor de Sync V1 e DTOs:** Criado `mobile/lib/features/sync/api/sync_dto.dart` com DTOs de decks/cards que fazem `DateTime.parse(...).toUtc()` antes de gerar `Companion` para Drift. Criado `mobile/lib/features/sync/sync_service.dart` com `pushPendingEvents()` para enviar fila local via `POST /api/sync`, marcar aceitos, registrar conflitos em `lastErrorJson`/`lastAttemptAt` e aplicar `server_state` com política Server Wins; e `pullChanges()` para buscar `GET /api/sync/changes` e aplicar upserts em lote no SQLite.
- [x] **Bloco 17 - Interface UI e Riverpod:** Criado `mobile/lib/core/providers.dart` com providers globais para `AppDatabase`, `Dio` e `SyncService`. Criadas `DecksScreen` e `ReviewScreen` conectando lista de decks, sync manual, revisão local com SM-2, update no Drift e enfileiramento de `SyncEvent` offline-first. Atualizado `mobile/lib/main.dart` com `ProviderScope` e home em `DecksScreen`.

### Dia 6 — 2026-04-28 (Web Dashboard & LaTeX)
- [x] **Inicialização Next.js Web:** Next.js inicializado em `web/` com App Router.
- [x] **Route Groups Web:** Estruturados `web/src/app/(marketing)` e `web/src/app/(app)/dashboard` com Root Layout em `web/src/app/layout.tsx`.
- [x] **KaTeX no Dashboard:** Configurado CSS global do KaTeX e componente `MathCard` com `react-katex` (`InlineMath`/`BlockMath`) para flashcards com LaTeX no Dashboard.
- [x] **Dashboard alinhado ao Wireframe:** Refatorada a tela `Meus decks` com navegação Synapse, grid de decks mockados (`trigonometria`, `botanica`, `eletromagnetismo`) e prova visual de KaTeX no card de eletromagnetismo.
- [x] **Tela de Revisão Web:** Criada `web/src/app/(app)/review/[deckId]/page.tsx` com layout vertical, flashcard grande, fluxo `Mostrar Resposta` e os 4 botões oficiais (`errei`, `dificil`, `bom`, `facil`) avançando entre cards mockados.
- [x] **Cliente HTTP Web:** Criado `web/src/lib/api.ts` com wrapper `fetch` apontando para `http://localhost:8000/api` e TODO para injeção de JWT no Dia 7.

### Dia 7 — 2026-04-28 (Autenticação e Segurança)
- [x] **Bloco 18 - Backend: validação do contrato JWT:** Finalizados `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh` retornando `{ access, refresh }`, criada rota protegida `GET /api/auth/me` com `AsyncJWTAuth`, e atualizados testes do fluxo completo de auth.
- [x] **Bloco 19 - Web: fundação de autenticação segura:** Criada tela `/login` em Next.js/Tailwind, BFF com Route Handlers para login/logout, persistência de `access` e `refresh` em cookies `httpOnly`, e `apiFetch` server-side com injeção automática do Bearer JWT.
- [x] **Bloco 20 - Web: proteção e integração de telas:** Criado middleware protegendo `/dashboard` e `/review`, Dashboard convertido para Server Component consumindo `GET /api/decks`, sessão de revisão integrada à fila real `GET /api/reviews/queue` e submissão SM-2 via BFF `POST /api/reviews`.
- [x] **Bloco 21 - Mobile: fluxo de autenticação e storage seguro:** Criados `AuthRepository`, `AuthController`, `LoginScreen` e `AuthGate`, tokens padronizados em `synapse_access_token`/`synapse_refresh_token` no `FlutterSecureStorage`, Dio lendo o access token padrão, e logout limpando tokens + tabelas Drift (`SyncEvents`, `LocalCards`, `LocalDecks`) para evitar dados fantasmas entre usuários.
- [x] **Bloco 22 - Mobile: Dio final + integração das telas:** `ApiClient` atualizado com `QueuedInterceptorsWrapper`, refresh token automático em 401, retry da requisição original com novo access token, logout forçado em falha de refresh e sync inicial na `DecksScreen` seguindo Push Pending → Pull Changes sem travar a UI offline.
- [x] **Bloco 23 - Verificação e documentação:** Auditoria teórica do fluxo Auth/Sync concluída. Confirmado desenho ponta a ponta com JWT no Django, BFF seguro no Next.js via cookies `httpOnly`, Mobile com `FlutterSecureStorage`, refresh automático e limpeza do banco local no logout. Riscos aceitos para MVP registrados em Issues / riscos abertos.

## 🟡 Em andamento
- Dia 8 iniciado. Foco atual: polimento de UI/UX Mobile/Web, filtros, estados visuais e animações leves.

## ⬜ Pendente — próximos dias
- Dia 8 (30/04): Polimento de UI Mobile (Filtros, Animações) e Web.
- Dia 9 (01/05): Landing Page Institucional.
- Dia 10 (02/05): Deploy final, E2E e Lançamento.

---

## 🏗 Arquitetura acordada (não mudar sem Tech Lead)
- **Backend:** Django 5.2 + Django Ninja + `django-ninja-jwt`.
- **DB:** Postgres 16 compartilhado.
- **Sync Model (Offline-First):** - API de Sync processa lotes offline de forma síncrona no backend (Temporal adiado para reduzir overhead neste momento).
  - **LWW (Last-Writer-Wins):** Conflitos resolvidos por `client_ts` vs `last_client_ts` da entidade. 
  - **Locks:** Serialização por `(user_id, entity_id)` via `pg_advisory_xact_lock`.
  - **Soft Deletes:** `deleted_at` gerencia exclusões e a API de Pull distribui os tombstones.

## 🔑 Decisões fixadas
- Produto: **Synapse**
- **Idempotência:** `SyncEvent.id` (UUID) atua como chave. Replays de rede exatos recebem a resposta do cache sem re-executar lógica de negócio ou corromper estado (Ex: retries de SM-2).
- **Relógios:** O Backend NUNCA confia no relógio do cliente para ordenação global, mas OBRIGA a comparação LWW baseada no relógio do cliente. Timezones (UTC) são estritamente validados.

## ⚠️ Issues / riscos abertos
- Integração do cliente móvel com a nova API de Sync demandará mapeamento cuidadoso de banco de dados local (ex: Drift no Flutter).
- A validação mobile final fica a cargo do desenvolvedor: rodar `flutter pub get`, `dart run build_runner build --delete-conflicting-outputs`, `flutter analyze` e os testes Flutter após regenerar os arquivos Drift.
- **Risco de CORS futuro:** hoje a Web usa BFF/Route Handlers do Next.js e não chama o Django direto do navegador. Se no futuro o frontend Web pular o BFF e chamar a API Django diretamente, será obrigatório configurar `django-cors-headers` de forma estrita, com origens explícitas e sem curingas em produção.
- **Edge case de refresh expirado no Mobile:** se `synapse_refresh_token` também expirar, o interceptor do Dio fará logout forçado e limpará o banco local Drift. Se o usuário tiver cards/reviews offline ainda não sincronizados, esses dados serão perdidos. Aceito para o MVP, mas deve ser revisitado antes de produção.
