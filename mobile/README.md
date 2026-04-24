# mobile/ — Synapse Mobile (Flutter, offline-first)

App Flutter que permite estudar offline e sincroniza de forma resiliente quando volta online.

## Responsabilidades
- Auth JWT (mesmo contrato do web; access + refresh persistidos seguramente).
- Listagem e detalhes de decks (read-only cache local).
- **Sessão de revisão offline**: executa SM-2 **localmente** na pilha de cards baixados; grava `Review` e `SyncEvent` no SQLite.
- **Sync bidirecional** via `POST /sync` — batch de `SyncEvent`s com `id` gerado pelo cliente (UUID v4/v7) = idempotency key.

## Escopo offline (fixado)
- **Permitido offline:** create card, review card.
- **Somente online:** update/delete de deck/card.
- **Conflitos:** LWW por `client_ts`, sem UI de merge.

## Stack
- Flutter 3.x + Dart
- **Drift** (SQLite tipado) para storage local
- **Dio** para HTTP (com interceptor de JWT + retry)
- **Riverpod** para state management
- `flutter_math_fork` para LaTeX (com fallback server-side se travar)
- `uuid` para gerar `SyncEvent.id` client-side
- Testes: `flutter_test` + `mocktail`

## Layout (a ser criado no Dia 7)
```
mobile/
├── pubspec.yaml
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── api/              # Dio + interceptors JWT
│   │   ├── db/               # Drift schema + DAOs
│   │   └── srs/              # SM-2 (mesma lógica da API, reimplementada em Dart)
│   ├── features/
│   │   ├── auth/
│   │   ├── decks/
│   │   ├── review/
│   │   └── sync/             # fila + worker de SyncEvent
│   └── app.dart
└── test/
```

## Dev
A partir do Dia 7:
```bash
cd mobile
flutter pub get
flutter run          # device/emulador
flutter test
```

## Riscos conhecidos
- **Sync edge cases**: mitigado por escopo apertado (só create+review offline).
- **LaTeX complexo em `flutter_math_fork`**: fallback é renderizar server-side para PNG.

> Ver `docs/TECH_SPECS.md` §4.1, §6 e §9.
