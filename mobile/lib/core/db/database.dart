import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'tables.dart';

part 'database.g.dart';

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final documentsDir = await getApplicationDocumentsDirectory();
    final dbFile = File(p.join(documentsDir.path, 'synapse.sqlite'));
    return NativeDatabase.createInBackground(dbFile);
  });
}

@DriftDatabase(
  tables: [LocalDecks, LocalCards, SyncEvents],
  daos: [LocalDeckDao, LocalCardDao, LocalSyncEventDao],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? _openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (migrator) => migrator.createAll(),
        beforeOpen: (details) async {
          await customStatement('PRAGMA foreign_keys = ON');
          await customStatement('PRAGMA journal_mode = WAL');
        },
      );
}

@DriftAccessor(tables: [LocalDecks])
class LocalDeckDao extends DatabaseAccessor<AppDatabase> with _$LocalDeckDaoMixin {
  LocalDeckDao(super.db);

  Future<List<LocalDeck>> getAllDecks({bool includeDeleted = false}) {
    final query = select(localDecks)..orderBy([(t) => OrderingTerm.asc(t.name)]);
    if (!includeDeleted) {
      query.where((t) => t.deletedAt.isNull());
    }
    return query.get();
  }

  Stream<List<LocalDeck>> watchDecks({bool includeDeleted = false}) {
    final query = select(localDecks)..orderBy([(t) => OrderingTerm.asc(t.name)]);
    if (!includeDeleted) {
      query.where((t) => t.deletedAt.isNull());
    }
    return query.watch();
  }

  Future<LocalDeck?> getDeckById(String id) {
    return (select(localDecks)..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  Future<void> upsertDeck(LocalDecksCompanion deck) async {
    await into(localDecks).insertOnConflictUpdate(deck);
  }

  Future<void> upsertDecks(Iterable<LocalDecksCompanion> decks) {
    final rows = decks.toList(growable: false);
    if (rows.isEmpty) {
      return Future.value();
    }
    return batch((batch) {
      batch.insertAllOnConflictUpdate(localDecks, rows);
    });
  }

  Future<int> markDeckDeleted({
    required String id,
    required DateTime deletedAt,
  }) {
    return (update(localDecks)..where((t) => t.id.equals(id))).write(
      LocalDecksCompanion(
        deletedAt: Value(deletedAt),
        updatedAt: Value(deletedAt),
      ),
    );
  }
}

@DriftAccessor(tables: [LocalCards])
class LocalCardDao extends DatabaseAccessor<AppDatabase> with _$LocalCardDaoMixin {
  LocalCardDao(super.db);

  Future<List<LocalCard>> getCardsForDeck(
    String deckId, {
    bool includeDeleted = false,
  }) {
    final query = select(localCards)
      ..where((t) {
        final deckFilter = t.deckId.equals(deckId);
        return includeDeleted ? deckFilter : deckFilter & t.deletedAt.isNull();
      })
      ..orderBy([(t) => OrderingTerm.asc(t.dueAt)]);
    return query.get();
  }

  Stream<List<LocalCard>> watchCardsForDeck(
    String deckId, {
    bool includeDeleted = false,
  }) {
    final query = select(localCards)
      ..where((t) {
        final deckFilter = t.deckId.equals(deckId);
        return includeDeleted ? deckFilter : deckFilter & t.deletedAt.isNull();
      })
      ..orderBy([(t) => OrderingTerm.asc(t.dueAt)]);
    return query.watch();
  }

  Future<List<LocalCard>> getDueCards({
    required DateTime nowUtc,
    String? deckId,
    int limit = 50,
  }) {
    final query = select(localCards)
      ..where((t) {
        final dueFilter =
            t.deletedAt.isNull() & t.dueAt.isSmallerOrEqualValue(nowUtc);
        final selectedDeckId = deckId;
        if (selectedDeckId == null) {
          return dueFilter;
        }
        return dueFilter & t.deckId.equals(selectedDeckId);
      })
      ..orderBy([(t) => OrderingTerm.asc(t.dueAt)])
      ..limit(limit);
    return query.get();
  }

  Future<LocalCard?> getCardById(String id) {
    return (select(localCards)..where((t) => t.id.equals(id))).getSingleOrNull();
  }

  Future<void> upsertCard(LocalCardsCompanion card) async {
    await into(localCards).insertOnConflictUpdate(card);
  }

  Future<void> upsertCards(Iterable<LocalCardsCompanion> cards) {
    final rows = cards.toList(growable: false);
    if (rows.isEmpty) {
      return Future.value();
    }
    return batch((batch) {
      batch.insertAllOnConflictUpdate(localCards, rows);
    });
  }

  Future<int> markCardDeleted({
    required String id,
    required DateTime deletedAt,
  }) {
    return (update(localCards)..where((t) => t.id.equals(id))).write(
      LocalCardsCompanion(
        deletedAt: Value(deletedAt),
        updatedAt: Value(deletedAt),
      ),
    );
  }
}

@DriftAccessor(tables: [SyncEvents])
class LocalSyncEventDao extends DatabaseAccessor<AppDatabase>
    with _$LocalSyncEventDaoMixin {
  LocalSyncEventDao(super.db);

  Future<void> enqueue(SyncEventsCompanion event) async {
    // insertOrIgnore — never overwrite an already-queued event row.
    // Event ids are immutable per the sync contract, so a re-enqueue
    // with the same id is necessarily a duplicate; upserting would
    // demote a 'sending'/'accepted' row back to a fresh 'queued' state
    // and risk a second send to the server. Ignoring the conflict
    // preserves the original row and its current state.
    await into(syncEvents)
        .insert(event, mode: InsertMode.insertOrIgnore);
  }

  Future<List<SyncEvent>> getPendingEvents({int limit = 100}) {
    final query = select(syncEvents)
      ..where(
        (t) => t.status.isIn([
          LocalSyncStatus.queued,
          LocalSyncStatus.sending,
        ]),
      )
      ..orderBy([(t) => OrderingTerm.asc(t.clientTs)])
      ..limit(limit);
    return query.get();
  }

  Stream<List<SyncEvent>> watchQueuedEvents() {
    final query = select(syncEvents)
      ..where((t) => t.status.equals(LocalSyncStatus.queued))
      ..orderBy([(t) => OrderingTerm.asc(t.clientTs)]);
    return query.watch();
  }

  Future<int> markSending(Iterable<String> ids) {
    final idList = ids.toList(growable: false);
    if (idList.isEmpty) {
      return Future.value(0);
    }
    return (update(syncEvents)..where((t) => t.id.isIn(idList))).write(
      const SyncEventsCompanion(status: Value(LocalSyncStatus.sending)),
    );
  }

  Future<int> markAccepted(String id) {
    return (update(syncEvents)..where((t) => t.id.equals(id))).write(
      const SyncEventsCompanion(status: Value(LocalSyncStatus.accepted)),
    );
  }

  Future<int> markConflict(
    String id, {
    required String serverResponse,
    required DateTime nowUtc,
  }) {
    return (update(syncEvents)..where((t) => t.id.equals(id))).write(
      SyncEventsCompanion(
        status: const Value(LocalSyncStatus.conflict),
        lastErrorJson: Value(serverResponse),
        lastAttemptAt: Value(nowUtc),
      ),
    );
  }

  Future<int> resetSendingToQueued() {
    return (update(syncEvents)
          ..where((t) => t.status.equals(LocalSyncStatus.sending)))
        .write(
      const SyncEventsCompanion(status: Value(LocalSyncStatus.queued)),
    );
  }

  Future<int> incrementRetryCount(String id) {
    return customUpdate(
      'UPDATE sync_events SET retry_count = retry_count + 1 WHERE id = ?',
      variables: [Variable.withString(id)],
      updates: {syncEvents},
    );
  }
}
