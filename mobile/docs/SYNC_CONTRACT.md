# Synapse Mobile Sync Contract

This document freezes the Day 5 mobile contract for the Flutter client. The
backend is the authority for tenant isolation, LWW conflict resolution, and
idempotent replay. The mobile app is responsible for durable local state,
client-generated event ids, timezone-aware UTC timestamps, and retry-safe
delivery.

## Official Cycle

1. Initial Pull
   - After login, the client calls `GET /api/sync/changes` without a cursor.
   - The response is applied to SQLite with upserts for live rows and tombstone
     application for `deleted_at != null`.
   - The client stores `next_cursor` when present and repeats until
     `has_more == false`.

2. Offline Work
   - The app may review cards offline and create cards offline.
   - Each offline action writes the local entity change and a durable
     `SyncEvent` row in the same local transaction.
   - `SyncEvent.id` is generated on the client and never changes.
   - `client_ts` must be ISO 8601 with timezone, normalized to UTC before
     serialization.

3. Push Pending
   - When online, the app sends queued events to `POST /api/sync` in batches.
   - Accepted events are marked as synced locally.
   - Conflicting events are marked as conflict and their `server_state` is
     applied locally when present.
   - Exact HTTP retries must resend the same event ids and payloads.

4. Incremental Pull
   - After every successful push batch, the app calls `GET /api/sync/changes`
     with the stored cursor until drained.
   - This catches server-side tombstones, changes from other devices, and
     authoritative states after conflict handling.

## Conflict Policy

MVP policy: Server Wins.

The backend resolves conflicts with Last-Writer-Wins over
`(client_ts, event_id)`. When the backend returns a conflict:

- No merge UI is shown in the MVP.
- If `server_state` is present, the local entity is overwritten with it.
- If `server_state` is null, the client keeps the event as failed/conflict for
  debug visibility and does not leak or infer foreign tenant data.
- The original event is never regenerated under the same id with a modified
  payload.

Offline MVP scope:

- Allowed offline: `review` card, `create` card.
- Online-only in MVP: update/delete deck, update/delete card.

## GET /api/sync/changes

Request without cursor:

```http
GET /api/sync/changes?limit=500
Authorization: Bearer <access-token>
```

Request with cursor:

```http
GET /api/sync/changes?cursor=MjAyNi0wNC0yN1QxMjozMDo0NS4xMjM0NTYrMDA6MDB8Y2FyZHxmN2Qw...&limit=500
Authorization: Bearer <access-token>
```

Canonical response:

```json
{
  "server_now": "2026-04-27T12:30:45.123456Z",
  "decks": [
    {
      "id": "2d9c8b50-7f65-4df0-a8f9-8e96ce59a01a",
      "name": "Biologia",
      "description": "Citologia e genetica",
      "is_public": false,
      "updated_at": "2026-04-27T12:20:00.000000Z",
      "deleted_at": null
    }
  ],
  "cards": [
    {
      "id": "f7d0c1d4-4637-4c61-93bd-9f8b9ac2f1c2",
      "deck_id": "2d9c8b50-7f65-4df0-a8f9-8e96ce59a01a",
      "front": "O que e osmose?",
      "back": "Movimento de agua atraves de membrana semipermeavel.",
      "state": "review",
      "ease_factor": 2.5,
      "interval_days": 10,
      "repetitions": 3,
      "due_at": "2026-04-27T09:00:00.000000Z",
      "updated_at": "2026-04-27T12:21:00.000000Z",
      "deleted_at": null
    }
  ],
  "has_more": false,
  "next_cursor": "MjAyNi0wNC0yN1QxMjoyMTowMC4wMDAwMDArMDA6MDB8Y2FyZHxmN2Qw..."
}
```

Tombstone example:

```json
{
  "id": "f7d0c1d4-4637-4c61-93bd-9f8b9ac2f1c2",
  "deck_id": "2d9c8b50-7f65-4df0-a8f9-8e96ce59a01a",
  "front": "O que e osmose?",
  "back": "Movimento de agua atraves de membrana semipermeavel.",
  "state": "review",
  "ease_factor": 2.5,
  "interval_days": 10,
  "repetitions": 3,
  "due_at": "2026-04-27T09:00:00.000000Z",
  "updated_at": "2026-04-27T12:40:00.000000Z",
  "deleted_at": "2026-04-27T12:40:00.000000Z"
}
```

## POST /api/sync

Canonical request with a `review` event and a `create` card event:

```http
POST /api/sync
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "device_id": "flutter-android-9f4b2d",
  "events": [
    {
      "id": "a0eb6f0b-f6a8-4e07-bef0-73e7fdf8d7a1",
      "op": "review",
      "entity_type": "card",
      "entity_id": "f7d0c1d4-4637-4c61-93bd-9f8b9ac2f1c2",
      "client_ts": "2026-04-27T13:00:00.000000Z",
      "payload": {
        "rating": "good",
        "duration_ms": 4200
      }
    },
    {
      "id": "2f5f25df-a15c-449e-b2bd-e34101f4734e",
      "op": "create",
      "entity_type": "card",
      "entity_id": "d98ca71c-a8d2-46d3-9102-c5c8f9c96f43",
      "client_ts": "2026-04-27T13:02:10.000000Z",
      "payload": {
        "deck_id": "2d9c8b50-7f65-4df0-a8f9-8e96ce59a01a",
        "front": "Qual organela produz ATP?",
        "back": "Mitocondria."
      }
    }
  ]
}
```

Canonical success response:

```json
{
  "accepted": [
    "a0eb6f0b-f6a8-4e07-bef0-73e7fdf8d7a1",
    "2f5f25df-a15c-449e-b2bd-e34101f4734e"
  ],
  "conflicts": []
}
```

Canonical conflict response:

```json
{
  "accepted": [
    "2f5f25df-a15c-449e-b2bd-e34101f4734e"
  ],
  "conflicts": [
    {
      "event_id": "a0eb6f0b-f6a8-4e07-bef0-73e7fdf8d7a1",
      "reason": "stale_event",
      "server_state": {
        "id": "f7d0c1d4-4637-4c61-93bd-9f8b9ac2f1c2",
        "deck_id": "2d9c8b50-7f65-4df0-a8f9-8e96ce59a01a",
        "front": "O que e osmose?",
        "back": "Movimento de agua atraves de membrana semipermeavel.",
        "state": "review",
        "ease_factor": 2.5,
        "interval_days": 25,
        "repetitions": 4,
        "due_at": "2026-05-22T13:00:00.000000Z",
        "updated_at": "2026-04-27T13:01:00.000000Z",
        "deleted_at": null
      }
    }
  ]
}
```

Validation rule:

`client_ts` without timezone, for example `"2026-04-27T13:00:00"`, is
invalid and the backend returns request validation error `422`.
