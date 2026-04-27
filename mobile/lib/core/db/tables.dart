import 'package:drift/drift.dart';

class UtcDateTimeConverter extends TypeConverter<DateTime, int> {
  const UtcDateTimeConverter();

  @override
  DateTime fromSql(int fromDb) {
    return DateTime.fromMicrosecondsSinceEpoch(fromDb, isUtc: true);
  }

  @override
  int toSql(DateTime value) {
    if (!value.isUtc) {
      throw ArgumentError.value(
        value,
        'value',
        'DateTime persisted in Drift must be UTC. Use DateTime.now().toUtc() '
            'or DateTime.parse(...Z).toUtc().',
      );
    }
    return value.microsecondsSinceEpoch;
  }
}

class LocalEntityType {
  const LocalEntityType._();

  static const deck = 'deck';
  static const card = 'card';

  static const values = [deck, card];
}

class LocalSyncOp {
  const LocalSyncOp._();

  static const create = 'create';
  static const update = 'update';
  static const delete = 'delete';
  static const review = 'review';

  static const values = [create, update, delete, review];
}

class LocalSyncStatus {
  const LocalSyncStatus._();

  static const queued = 'queued';
  static const sending = 'sending';
  static const accepted = 'accepted';
  static const conflict = 'conflict';

  static const values = [queued, sending, accepted, conflict];
}

class LocalCardState {
  const LocalCardState._();

  static const newCard = 'new';
  static const learning = 'learning';
  static const review = 'review';
  static const lapsed = 'lapsed';

  static const values = [newCard, learning, review, lapsed];
}

class LocalDecks extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text()();
  BoolColumn get isPublic => boolean()();
  IntColumn get updatedAt => integer().map(const UtcDateTimeConverter())();
  IntColumn get deletedAt =>
      integer().map(const UtcDateTimeConverter()).nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class LocalCards extends Table {
  TextColumn get id => text()();
  TextColumn get deckId => text()();
  TextColumn get front => text()();
  TextColumn get back => text()();
  TextColumn get state => text().check(state.isIn(LocalCardState.values))();
  RealColumn get easeFactor =>
      real().check(easeFactor.isBiggerOrEqualValue(1.3))();
  IntColumn get intervalDays =>
      integer().check(intervalDays.isBiggerOrEqualValue(0))();
  IntColumn get repetitions =>
      integer().check(repetitions.isBiggerOrEqualValue(0))();
  IntColumn get dueAt => integer().map(const UtcDateTimeConverter())();
  IntColumn get updatedAt => integer().map(const UtcDateTimeConverter())();
  IntColumn get deletedAt =>
      integer().map(const UtcDateTimeConverter()).nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncEvents extends Table {
  TextColumn get id => text()();
  TextColumn get entityType =>
      text().check(entityType.isIn(LocalEntityType.values))();
  TextColumn get entityId => text()();
  TextColumn get op => text().check(op.isIn(LocalSyncOp.values))();
  TextColumn get payloadJson => text()();
  IntColumn get clientTs => integer().map(const UtcDateTimeConverter())();
  TextColumn get status => text()
      .check(status.isIn(LocalSyncStatus.values))
      .withDefault(const Constant(LocalSyncStatus.queued))();
  IntColumn get retryCount => integer()
      .check(retryCount.isBiggerOrEqualValue(0))
      .withDefault(const Constant(0))();

  @override
  Set<Column> get primaryKey => {id};
}
