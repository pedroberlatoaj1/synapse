# STATE.md — Synapse

> **Memória operacional do projeto.** Atualizado a cada bloco.
> Qualquer IA (principal ou auxiliar) que vá codar DEVE ler este arquivo primeiro,
> junto com `docs/PRD.md` e `docs/TECH_SPECS.md`.

**Produto:** Synapse — SRS para estudantes de alta performance
**Case:** 10 dias (24/04 – 04/05/2026)
**Última atualização:** 2026-04-27 — Blocos 12 e 13 concluídos. Dia 5 foi direcionado para Mobile Foundation. Contrato Mobile-Sync congelado em `mobile/docs/SYNC_CONTRACT.md`, fixtures de paridade SM-2 criadas em `mobile/docs/sm2_fixtures.json`, e app Flutter inicial scaffoldado em `mobile/` com dependências, estrutura `lib/` e client Dio preparado para Bearer Token.

---

## 📍 Dia corrente: **Dia 5 — Mobile Foundation**

### Status: ✅ Blocos 12 e 13 concluídos

### Objetivo do dia
Construir a fundação do cliente Flutter offline-first: contrato de sincronização, fixtures de paridade SM-2, bootstrap do app, estrutura base, dependências móveis e client HTTP pronto para JWT.

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

## 🟡 Em andamento
- Aguardando definição do próximo bloco mobile (provável Bloco 14: Drift schema local + DAOs).

## ⬜ Pendente — próximos dias
- Dia 5 (28/04): Próximo alvo mobile a aprovar: banco local Drift, DAOs e metadados de sync.
- Dia 6 (29/04): Sessão de revisão web + dashboard + LaTeX
- Dia 7 (30/04): Flutter bootstrap + auth + lista decks
- Dia 8 (01/05): Sessão offline mobile + sync
- Dia 9 (02/05): Landing page + polish
- Dia 10 (03/05): Deploy + vídeo + smoke E2E

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
- Ambiente desta sessão não possui `flutter`/FVM no PATH. O scaffold Flutter do Bloco 13 foi criado manualmente com os arquivos essenciais; validar com `flutter pub get` e `flutter analyze` assim que o SDK Flutter estiver disponível.
