import 'dart:convert';

import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/core/db/tables.dart';
import 'package:uuid/uuid.dart';

/// Single write-path for the Decks feature.
///
/// All mutations go through here so we can guarantee the offline-first
/// invariant: a local row and its outbound `sync_event` are always
/// persisted together (or not at all).
class DeckRepository {
  DeckRepository(this._db) : _uuid = const Uuid();

  final AppDatabase _db;
  final Uuid _uuid;

  /// Reactive stream backing the Home screen. Drift re-emits whenever
  /// `local_decks` changes — from local writes, sync pulls, or logout wipe.
  Stream<List<LocalDeck>> watchDecks() => _db.localDeckDao.watchDecks();

  /// Creates a deck locally and enqueues the corresponding sync event.
  ///
  /// Returns the freshly-generated deck id.
  Future<String> createDeck({
    required String name,
    String description = '',
  }) {
    final deckId = _uuid.v4();
    final eventId = _uuid.v4();
    final now = DateTime.now().toUtc();

    // Atomic boundary: the deck row and its `sync_event` must land
    // together. If either insert throws, Drift rolls back the whole
    // transaction — we never leave a deck without its outbound event,
    // and we never enqueue an event that points at a non-existent row.
    return _db.transaction<String>(() async {
      await _db.localDeckDao.upsertDeck(
        LocalDecksCompanion.insert(
          id: deckId,
          name: name,
          description: description,
          isPublic: false,
          updatedAt: now,
        ),
      );

      // Payload shape mirrors what `DeckSyncDto.fromJson` expects on the
      // wire (snake_case keys, ISO-8601 UTC timestamps), so the server
      // can hydrate it without translation.
      final payload = <String, Object?>{
        'id': deckId,
        'name': name,
        'description': description,
        'is_public': false,
        'updated_at': now.toIso8601String(),
        'deleted_at': null,
      };

      await _db.localSyncEventDao.enqueue(
        SyncEventsCompanion.insert(
          id: eventId,
          entityType: LocalEntityType.deck,
          entityId: deckId,
          op: LocalSyncOp.create,
          payloadJson: jsonEncode(payload),
          clientTs: now,
        ),
      );

      return deckId;
    });
  }
}
