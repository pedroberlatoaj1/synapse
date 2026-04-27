import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/core/db/tables.dart';
import 'package:synapse_mobile/features/sync/api/sync_dto.dart';

typedef UtcNow = DateTime Function();

class SyncService {
  SyncService({
    required AppDatabase database,
    required Dio dio,
    required String deviceId,
    UtcNow? nowUtc,
  })  : _database = database,
        _dio = dio,
        _deviceId = deviceId,
        _nowUtc = nowUtc ?? (() => DateTime.now().toUtc());

  final AppDatabase _database;
  final Dio _dio;
  final String _deviceId;
  final UtcNow _nowUtc;

  Future<PushSyncResult> pushPendingEvents({int limit = 100}) async {
    final events = await _database.localSyncEventDao.getPendingEvents(
      limit: limit,
    );
    if (events.isEmpty) {
      return const PushSyncResult(
        attempted: 0,
        acceptedIds: [],
        conflicts: [],
      );
    }

    final eventIds = events.map((event) => event.id).toList(growable: false);
    await _database.localSyncEventDao.markSending(eventIds);

    final response = await _dio.post<Object?>(
      '/api/sync',
      data: {
        'device_id': _deviceId,
        'events': events.map(_eventToJson).toList(growable: false),
      },
    );
    final pushResponse = _PushResponseDto.fromJson(_responseObject(response.data));
    final eventsById = {for (final event in events) event.id: event};

    await _database.transaction(() async {
      for (final acceptedId in pushResponse.acceptedIds) {
        await _database.localSyncEventDao.markAccepted(acceptedId);
      }

      for (final conflict in pushResponse.conflicts) {
        final event = eventsById[conflict.eventId];
        await _database.localSyncEventDao.markConflict(
          conflict.eventId,
          serverResponse: jsonEncode(conflict.rawJson),
          nowUtc: _nowUtc().toUtc(),
        );

        if (event != null && conflict.serverState != null) {
          await _applyServerState(event, conflict.serverState!);
        }
      }
    });

    return PushSyncResult(
      attempted: events.length,
      acceptedIds: pushResponse.acceptedIds,
      conflicts: pushResponse.conflicts
          .map(
            (conflict) => PushConflictResult(
              eventId: conflict.eventId,
              reason: conflict.reason,
              hasServerState: conflict.serverState != null,
            ),
          )
          .toList(growable: false),
    );
  }

  Future<PullChangesResult> pullChanges({
    String? cursor,
    int limit = 500,
  }) async {
    final response = await _dio.get<Object?>(
      '/api/sync/changes',
      queryParameters: {
        'limit': limit,
        if (cursor != null && cursor.isNotEmpty) 'cursor': cursor,
      },
    );
    final pullResponse = SyncPullResponseDto.fromJson(
      _responseObject(response.data),
    );

    await _database.transaction(() async {
      await _database.localDeckDao.upsertDecks(
        pullResponse.decks.map((deck) => deck.toCompanion()),
      );
      await _database.localCardDao.upsertCards(
        pullResponse.cards.map((card) => card.toCompanion()),
      );
    });

    return PullChangesResult(
      serverNow: pullResponse.serverNow,
      deckCount: pullResponse.decks.length,
      cardCount: pullResponse.cards.length,
      hasMore: pullResponse.hasMore,
      nextCursor: pullResponse.nextCursor,
    );
  }

  Map<String, Object?> _eventToJson(SyncEvent event) {
    return {
      'id': event.id,
      'op': event.op,
      'entity_type': event.entityType,
      'entity_id': event.entityId,
      'client_ts': event.clientTs.toUtc().toIso8601String(),
      'payload': _decodePayload(event.payloadJson),
    };
  }

  Future<void> _applyServerState(
    SyncEvent event,
    Map<String, Object?> serverState,
  ) async {
    if (event.entityType == LocalEntityType.deck) {
      await _database.localDeckDao.upsertDeck(
        DeckSyncDto.fromJson(serverState).toCompanion(),
      );
      return;
    }

    if (event.entityType == LocalEntityType.card) {
      await _database.localCardDao.upsertCard(
        CardSyncDto.fromJson(serverState).toCompanion(),
      );
    }
  }
}

class PushSyncResult {
  const PushSyncResult({
    required this.attempted,
    required this.acceptedIds,
    required this.conflicts,
  });

  final int attempted;
  final List<String> acceptedIds;
  final List<PushConflictResult> conflicts;
}

class PushConflictResult {
  const PushConflictResult({
    required this.eventId,
    required this.reason,
    required this.hasServerState,
  });

  final String eventId;
  final String reason;
  final bool hasServerState;
}

class PullChangesResult {
  const PullChangesResult({
    required this.serverNow,
    required this.deckCount,
    required this.cardCount,
    required this.hasMore,
    required this.nextCursor,
  });

  final DateTime serverNow;
  final int deckCount;
  final int cardCount;
  final bool hasMore;
  final String? nextCursor;
}

class _PushResponseDto {
  const _PushResponseDto({
    required this.acceptedIds,
    required this.conflicts,
  });

  factory _PushResponseDto.fromJson(Map<String, Object?> json) {
    final accepted = json['accepted'];
    final conflicts = json['conflicts'];

    if (accepted is! List) {
      throw const FormatException('Expected "accepted" to be a list.');
    }
    if (conflicts is! List) {
      throw const FormatException('Expected "conflicts" to be a list.');
    }

    return _PushResponseDto(
      acceptedIds: accepted.map((id) => id.toString()).toList(growable: false),
      conflicts: conflicts
          .map((item) => _PushConflictDto.fromJson(_object(item)))
          .toList(growable: false),
    );
  }

  final List<String> acceptedIds;
  final List<_PushConflictDto> conflicts;
}

class _PushConflictDto {
  const _PushConflictDto({
    required this.eventId,
    required this.reason,
    required this.serverState,
    required this.rawJson,
  });

  factory _PushConflictDto.fromJson(Map<String, Object?> json) {
    final serverState = json['server_state'];
    return _PushConflictDto(
      eventId: _string(json, 'event_id'),
      reason: _string(json, 'reason'),
      serverState: serverState == null ? null : _object(serverState),
      rawJson: json,
    );
  }

  final String eventId;
  final String reason;
  final Map<String, Object?>? serverState;
  final Map<String, Object?> rawJson;
}

Map<String, Object?> _responseObject(Object? data) {
  if (data is String) {
    return _object(jsonDecode(data));
  }
  return _object(data);
}

Map<String, Object?> _decodePayload(String payloadJson) {
  return _object(jsonDecode(payloadJson));
}

Map<String, Object?> _object(Object? value) {
  if (value is Map<String, Object?>) {
    return value;
  }
  if (value is Map) {
    return value.cast<String, Object?>();
  }
  throw const FormatException('Expected JSON object.');
}

String _string(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is String) {
    return value;
  }
  throw FormatException('Expected "$key" to be a string.');
}
