import 'package:drift/drift.dart';
import 'package:synapse_mobile/core/db/database.dart';

class DeckSyncDto {
  const DeckSyncDto({
    required this.id,
    required this.name,
    required this.description,
    required this.isPublic,
    required this.updatedAt,
    required this.deletedAt,
  });

  factory DeckSyncDto.fromJson(Map<String, Object?> json) {
    return DeckSyncDto(
      id: _readString(json, 'id'),
      name: _readString(json, 'name'),
      description: _readString(json, 'description'),
      isPublic: _readBool(json, 'is_public'),
      updatedAt: _readUtcDateTime(json, 'updated_at'),
      deletedAt: _readNullableUtcDateTime(json, 'deleted_at'),
    );
  }

  final String id;
  final String name;
  final String description;
  final bool isPublic;
  final DateTime updatedAt;
  final DateTime? deletedAt;

  LocalDecksCompanion toCompanion() {
    return LocalDecksCompanion(
      id: Value(id),
      name: Value(name),
      description: Value(description),
      isPublic: Value(isPublic),
      updatedAt: Value(updatedAt),
      deletedAt: Value(deletedAt),
    );
  }
}

class CardSyncDto {
  const CardSyncDto({
    required this.id,
    required this.deckId,
    required this.front,
    required this.back,
    required this.state,
    required this.easeFactor,
    required this.intervalDays,
    required this.repetitions,
    required this.dueAt,
    required this.updatedAt,
    required this.deletedAt,
  });

  factory CardSyncDto.fromJson(Map<String, Object?> json) {
    return CardSyncDto(
      id: _readString(json, 'id'),
      deckId: _readString(json, 'deck_id'),
      front: _readString(json, 'front'),
      back: _readString(json, 'back'),
      state: _readString(json, 'state'),
      easeFactor: _readNum(json, 'ease_factor').toDouble(),
      intervalDays: _readInt(json, 'interval_days'),
      repetitions: _readInt(json, 'repetitions'),
      dueAt: _readUtcDateTime(json, 'due_at'),
      updatedAt: _readUtcDateTime(json, 'updated_at'),
      deletedAt: _readNullableUtcDateTime(json, 'deleted_at'),
    );
  }

  final String id;
  final String deckId;
  final String front;
  final String back;
  final String state;
  final double easeFactor;
  final int intervalDays;
  final int repetitions;
  final DateTime dueAt;
  final DateTime updatedAt;
  final DateTime? deletedAt;

  LocalCardsCompanion toCompanion() {
    return LocalCardsCompanion(
      id: Value(id),
      deckId: Value(deckId),
      front: Value(front),
      back: Value(back),
      state: Value(state),
      easeFactor: Value(easeFactor),
      intervalDays: Value(intervalDays),
      repetitions: Value(repetitions),
      dueAt: Value(dueAt),
      updatedAt: Value(updatedAt),
      deletedAt: Value(deletedAt),
    );
  }
}

class SyncPullResponseDto {
  const SyncPullResponseDto({
    required this.serverNow,
    required this.decks,
    required this.cards,
    required this.hasMore,
    required this.nextCursor,
  });

  factory SyncPullResponseDto.fromJson(Map<String, Object?> json) {
    return SyncPullResponseDto(
      serverNow: _readUtcDateTime(json, 'server_now'),
      decks: _readObjectList(json, 'decks')
          .map(DeckSyncDto.fromJson)
          .toList(growable: false),
      cards: _readObjectList(json, 'cards')
          .map(CardSyncDto.fromJson)
          .toList(growable: false),
      hasMore: _readBool(json, 'has_more'),
      nextCursor: _readNullableString(json, 'next_cursor'),
    );
  }

  final DateTime serverNow;
  final List<DeckSyncDto> decks;
  final List<CardSyncDto> cards;
  final bool hasMore;
  final String? nextCursor;
}

DateTime _readUtcDateTime(Map<String, Object?> json, String key) {
  final value = _readString(json, key);
  return DateTime.parse(value).toUtc();
}

DateTime? _readNullableUtcDateTime(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value == null) {
    return null;
  }
  if (value is! String) {
    throw FormatException('Expected "$key" to be an ISO 8601 string or null.');
  }
  return DateTime.parse(value).toUtc();
}

String _readString(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is String) {
    return value;
  }
  throw FormatException('Expected "$key" to be a string.');
}

String? _readNullableString(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value == null || value is String) {
    return value as String?;
  }
  throw FormatException('Expected "$key" to be a string or null.');
}

bool _readBool(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is bool) {
    return value;
  }
  throw FormatException('Expected "$key" to be a boolean.');
}

num _readNum(Map<String, Object?> json, String key) {
  final value = json[key];
  if (value is num) {
    return value;
  }
  throw FormatException('Expected "$key" to be a number.');
}

int _readInt(Map<String, Object?> json, String key) {
  final value = _readNum(json, key);
  if (value is int) {
    return value;
  }
  if (value % 1 == 0) {
    return value.toInt();
  }
  throw FormatException('Expected "$key" to be an integer.');
}

List<Map<String, Object?>> _readObjectList(
  Map<String, Object?> json,
  String key,
) {
  final value = json[key];
  if (value is! List) {
    throw FormatException('Expected "$key" to be a list.');
  }

  return value.map((item) {
    if (item is Map<String, Object?>) {
      return item;
    }
    if (item is Map) {
      return item.cast<String, Object?>();
    }
    throw FormatException('Expected every "$key" item to be an object.');
  }).toList(growable: false);
}
