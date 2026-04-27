// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $LocalDecksTable extends LocalDecks
    with TableInfo<$LocalDecksTable, LocalDeck> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalDecksTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
      'name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _isPublicMeta =
      const VerificationMeta('isPublic');
  @override
  late final GeneratedColumn<bool> isPublic = GeneratedColumn<bool>(
      'is_public', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("is_public" IN (0, 1))'));
  @override
  late final GeneratedColumnWithTypeConverter<DateTime, int> updatedAt =
      GeneratedColumn<int>('updated_at', aliasedName, false,
              type: DriftSqlType.int, requiredDuringInsert: true)
          .withConverter<DateTime>($LocalDecksTable.$converterupdatedAt);
  @override
  late final GeneratedColumnWithTypeConverter<DateTime?, int> deletedAt =
      GeneratedColumn<int>('deleted_at', aliasedName, true,
              type: DriftSqlType.int, requiredDuringInsert: false)
          .withConverter<DateTime?>($LocalDecksTable.$converterdeletedAtn);
  @override
  List<GeneratedColumn> get $columns =>
      [id, name, description, isPublic, updatedAt, deletedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_decks';
  @override
  VerificationContext validateIntegrity(Insertable<LocalDeck> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
          _nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    } else if (isInserting) {
      context.missing(_descriptionMeta);
    }
    if (data.containsKey('is_public')) {
      context.handle(_isPublicMeta,
          isPublic.isAcceptableOrUnknown(data['is_public']!, _isPublicMeta));
    } else if (isInserting) {
      context.missing(_isPublicMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalDeck map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalDeck(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      name: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}name'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description'])!,
      isPublic: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}is_public'])!,
      updatedAt: $LocalDecksTable.$converterupdatedAt.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}updated_at'])!),
      deletedAt: $LocalDecksTable.$converterdeletedAtn.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}deleted_at'])),
    );
  }

  @override
  $LocalDecksTable createAlias(String alias) {
    return $LocalDecksTable(attachedDatabase, alias);
  }

  static TypeConverter<DateTime, int> $converterupdatedAt =
      const UtcDateTimeConverter();
  static TypeConverter<DateTime, int> $converterdeletedAt =
      const UtcDateTimeConverter();
  static TypeConverter<DateTime?, int?> $converterdeletedAtn =
      NullAwareTypeConverter.wrap($converterdeletedAt);
}

class LocalDeck extends DataClass implements Insertable<LocalDeck> {
  final String id;
  final String name;
  final String description;
  final bool isPublic;
  final DateTime updatedAt;
  final DateTime? deletedAt;
  const LocalDeck(
      {required this.id,
      required this.name,
      required this.description,
      required this.isPublic,
      required this.updatedAt,
      this.deletedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    map['description'] = Variable<String>(description);
    map['is_public'] = Variable<bool>(isPublic);
    {
      map['updated_at'] =
          Variable<int>($LocalDecksTable.$converterupdatedAt.toSql(updatedAt));
    }
    if (!nullToAbsent || deletedAt != null) {
      map['deleted_at'] =
          Variable<int>($LocalDecksTable.$converterdeletedAtn.toSql(deletedAt));
    }
    return map;
  }

  LocalDecksCompanion toCompanion(bool nullToAbsent) {
    return LocalDecksCompanion(
      id: Value(id),
      name: Value(name),
      description: Value(description),
      isPublic: Value(isPublic),
      updatedAt: Value(updatedAt),
      deletedAt: deletedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(deletedAt),
    );
  }

  factory LocalDeck.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalDeck(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      description: serializer.fromJson<String>(json['description']),
      isPublic: serializer.fromJson<bool>(json['isPublic']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      deletedAt: serializer.fromJson<DateTime?>(json['deletedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'description': serializer.toJson<String>(description),
      'isPublic': serializer.toJson<bool>(isPublic),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'deletedAt': serializer.toJson<DateTime?>(deletedAt),
    };
  }

  LocalDeck copyWith(
          {String? id,
          String? name,
          String? description,
          bool? isPublic,
          DateTime? updatedAt,
          Value<DateTime?> deletedAt = const Value.absent()}) =>
      LocalDeck(
        id: id ?? this.id,
        name: name ?? this.name,
        description: description ?? this.description,
        isPublic: isPublic ?? this.isPublic,
        updatedAt: updatedAt ?? this.updatedAt,
        deletedAt: deletedAt.present ? deletedAt.value : this.deletedAt,
      );
  LocalDeck copyWithCompanion(LocalDecksCompanion data) {
    return LocalDeck(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      description:
          data.description.present ? data.description.value : this.description,
      isPublic: data.isPublic.present ? data.isPublic.value : this.isPublic,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      deletedAt: data.deletedAt.present ? data.deletedAt.value : this.deletedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalDeck(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('isPublic: $isPublic, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, name, description, isPublic, updatedAt, deletedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalDeck &&
          other.id == this.id &&
          other.name == this.name &&
          other.description == this.description &&
          other.isPublic == this.isPublic &&
          other.updatedAt == this.updatedAt &&
          other.deletedAt == this.deletedAt);
}

class LocalDecksCompanion extends UpdateCompanion<LocalDeck> {
  final Value<String> id;
  final Value<String> name;
  final Value<String> description;
  final Value<bool> isPublic;
  final Value<DateTime> updatedAt;
  final Value<DateTime?> deletedAt;
  final Value<int> rowid;
  const LocalDecksCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.description = const Value.absent(),
    this.isPublic = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.deletedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalDecksCompanion.insert({
    required String id,
    required String name,
    required String description,
    required bool isPublic,
    required DateTime updatedAt,
    this.deletedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        name = Value(name),
        description = Value(description),
        isPublic = Value(isPublic),
        updatedAt = Value(updatedAt);
  static Insertable<LocalDeck> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? description,
    Expression<bool>? isPublic,
    Expression<int>? updatedAt,
    Expression<int>? deletedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (description != null) 'description': description,
      if (isPublic != null) 'is_public': isPublic,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (deletedAt != null) 'deleted_at': deletedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalDecksCompanion copyWith(
      {Value<String>? id,
      Value<String>? name,
      Value<String>? description,
      Value<bool>? isPublic,
      Value<DateTime>? updatedAt,
      Value<DateTime?>? deletedAt,
      Value<int>? rowid}) {
    return LocalDecksCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      isPublic: isPublic ?? this.isPublic,
      updatedAt: updatedAt ?? this.updatedAt,
      deletedAt: deletedAt ?? this.deletedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (isPublic.present) {
      map['is_public'] = Variable<bool>(isPublic.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<int>(
          $LocalDecksTable.$converterupdatedAt.toSql(updatedAt.value));
    }
    if (deletedAt.present) {
      map['deleted_at'] = Variable<int>(
          $LocalDecksTable.$converterdeletedAtn.toSql(deletedAt.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalDecksCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('isPublic: $isPublic, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalCardsTable extends LocalCards
    with TableInfo<$LocalCardsTable, LocalCard> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalCardsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _deckIdMeta = const VerificationMeta('deckId');
  @override
  late final GeneratedColumn<String> deckId = GeneratedColumn<String>(
      'deck_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _frontMeta = const VerificationMeta('front');
  @override
  late final GeneratedColumn<String> front = GeneratedColumn<String>(
      'front', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _backMeta = const VerificationMeta('back');
  @override
  late final GeneratedColumn<String> back = GeneratedColumn<String>(
      'back', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _stateMeta = const VerificationMeta('state');
  @override
  late final GeneratedColumn<String> state = GeneratedColumn<String>(
      'state', aliasedName, false,
      check: () => state.isIn(LocalCardState.values),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _easeFactorMeta =
      const VerificationMeta('easeFactor');
  @override
  late final GeneratedColumn<double> easeFactor = GeneratedColumn<double>(
      'ease_factor', aliasedName, false,
      check: () => ComparableExpr(easeFactor).isBiggerOrEqualValue(1.3),
      type: DriftSqlType.double,
      requiredDuringInsert: true);
  static const VerificationMeta _intervalDaysMeta =
      const VerificationMeta('intervalDays');
  @override
  late final GeneratedColumn<int> intervalDays = GeneratedColumn<int>(
      'interval_days', aliasedName, false,
      check: () => ComparableExpr(intervalDays).isBiggerOrEqualValue(0),
      type: DriftSqlType.int,
      requiredDuringInsert: true);
  static const VerificationMeta _repetitionsMeta =
      const VerificationMeta('repetitions');
  @override
  late final GeneratedColumn<int> repetitions = GeneratedColumn<int>(
      'repetitions', aliasedName, false,
      check: () => ComparableExpr(repetitions).isBiggerOrEqualValue(0),
      type: DriftSqlType.int,
      requiredDuringInsert: true);
  @override
  late final GeneratedColumnWithTypeConverter<DateTime, int> dueAt =
      GeneratedColumn<int>('due_at', aliasedName, false,
              type: DriftSqlType.int, requiredDuringInsert: true)
          .withConverter<DateTime>($LocalCardsTable.$converterdueAt);
  @override
  late final GeneratedColumnWithTypeConverter<DateTime, int> updatedAt =
      GeneratedColumn<int>('updated_at', aliasedName, false,
              type: DriftSqlType.int, requiredDuringInsert: true)
          .withConverter<DateTime>($LocalCardsTable.$converterupdatedAt);
  @override
  late final GeneratedColumnWithTypeConverter<DateTime?, int> deletedAt =
      GeneratedColumn<int>('deleted_at', aliasedName, true,
              type: DriftSqlType.int, requiredDuringInsert: false)
          .withConverter<DateTime?>($LocalCardsTable.$converterdeletedAtn);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        deckId,
        front,
        back,
        state,
        easeFactor,
        intervalDays,
        repetitions,
        dueAt,
        updatedAt,
        deletedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_cards';
  @override
  VerificationContext validateIntegrity(Insertable<LocalCard> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('deck_id')) {
      context.handle(_deckIdMeta,
          deckId.isAcceptableOrUnknown(data['deck_id']!, _deckIdMeta));
    } else if (isInserting) {
      context.missing(_deckIdMeta);
    }
    if (data.containsKey('front')) {
      context.handle(
          _frontMeta, front.isAcceptableOrUnknown(data['front']!, _frontMeta));
    } else if (isInserting) {
      context.missing(_frontMeta);
    }
    if (data.containsKey('back')) {
      context.handle(
          _backMeta, back.isAcceptableOrUnknown(data['back']!, _backMeta));
    } else if (isInserting) {
      context.missing(_backMeta);
    }
    if (data.containsKey('state')) {
      context.handle(
          _stateMeta, state.isAcceptableOrUnknown(data['state']!, _stateMeta));
    } else if (isInserting) {
      context.missing(_stateMeta);
    }
    if (data.containsKey('ease_factor')) {
      context.handle(
          _easeFactorMeta,
          easeFactor.isAcceptableOrUnknown(
              data['ease_factor']!, _easeFactorMeta));
    } else if (isInserting) {
      context.missing(_easeFactorMeta);
    }
    if (data.containsKey('interval_days')) {
      context.handle(
          _intervalDaysMeta,
          intervalDays.isAcceptableOrUnknown(
              data['interval_days']!, _intervalDaysMeta));
    } else if (isInserting) {
      context.missing(_intervalDaysMeta);
    }
    if (data.containsKey('repetitions')) {
      context.handle(
          _repetitionsMeta,
          repetitions.isAcceptableOrUnknown(
              data['repetitions']!, _repetitionsMeta));
    } else if (isInserting) {
      context.missing(_repetitionsMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalCard map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalCard(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      deckId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}deck_id'])!,
      front: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}front'])!,
      back: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}back'])!,
      state: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}state'])!,
      easeFactor: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}ease_factor'])!,
      intervalDays: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}interval_days'])!,
      repetitions: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}repetitions'])!,
      dueAt: $LocalCardsTable.$converterdueAt.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}due_at'])!),
      updatedAt: $LocalCardsTable.$converterupdatedAt.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}updated_at'])!),
      deletedAt: $LocalCardsTable.$converterdeletedAtn.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}deleted_at'])),
    );
  }

  @override
  $LocalCardsTable createAlias(String alias) {
    return $LocalCardsTable(attachedDatabase, alias);
  }

  static TypeConverter<DateTime, int> $converterdueAt =
      const UtcDateTimeConverter();
  static TypeConverter<DateTime, int> $converterupdatedAt =
      const UtcDateTimeConverter();
  static TypeConverter<DateTime, int> $converterdeletedAt =
      const UtcDateTimeConverter();
  static TypeConverter<DateTime?, int?> $converterdeletedAtn =
      NullAwareTypeConverter.wrap($converterdeletedAt);
}

class LocalCard extends DataClass implements Insertable<LocalCard> {
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
  const LocalCard(
      {required this.id,
      required this.deckId,
      required this.front,
      required this.back,
      required this.state,
      required this.easeFactor,
      required this.intervalDays,
      required this.repetitions,
      required this.dueAt,
      required this.updatedAt,
      this.deletedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['deck_id'] = Variable<String>(deckId);
    map['front'] = Variable<String>(front);
    map['back'] = Variable<String>(back);
    map['state'] = Variable<String>(state);
    map['ease_factor'] = Variable<double>(easeFactor);
    map['interval_days'] = Variable<int>(intervalDays);
    map['repetitions'] = Variable<int>(repetitions);
    {
      map['due_at'] =
          Variable<int>($LocalCardsTable.$converterdueAt.toSql(dueAt));
    }
    {
      map['updated_at'] =
          Variable<int>($LocalCardsTable.$converterupdatedAt.toSql(updatedAt));
    }
    if (!nullToAbsent || deletedAt != null) {
      map['deleted_at'] =
          Variable<int>($LocalCardsTable.$converterdeletedAtn.toSql(deletedAt));
    }
    return map;
  }

  LocalCardsCompanion toCompanion(bool nullToAbsent) {
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
      deletedAt: deletedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(deletedAt),
    );
  }

  factory LocalCard.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalCard(
      id: serializer.fromJson<String>(json['id']),
      deckId: serializer.fromJson<String>(json['deckId']),
      front: serializer.fromJson<String>(json['front']),
      back: serializer.fromJson<String>(json['back']),
      state: serializer.fromJson<String>(json['state']),
      easeFactor: serializer.fromJson<double>(json['easeFactor']),
      intervalDays: serializer.fromJson<int>(json['intervalDays']),
      repetitions: serializer.fromJson<int>(json['repetitions']),
      dueAt: serializer.fromJson<DateTime>(json['dueAt']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      deletedAt: serializer.fromJson<DateTime?>(json['deletedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'deckId': serializer.toJson<String>(deckId),
      'front': serializer.toJson<String>(front),
      'back': serializer.toJson<String>(back),
      'state': serializer.toJson<String>(state),
      'easeFactor': serializer.toJson<double>(easeFactor),
      'intervalDays': serializer.toJson<int>(intervalDays),
      'repetitions': serializer.toJson<int>(repetitions),
      'dueAt': serializer.toJson<DateTime>(dueAt),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'deletedAt': serializer.toJson<DateTime?>(deletedAt),
    };
  }

  LocalCard copyWith(
          {String? id,
          String? deckId,
          String? front,
          String? back,
          String? state,
          double? easeFactor,
          int? intervalDays,
          int? repetitions,
          DateTime? dueAt,
          DateTime? updatedAt,
          Value<DateTime?> deletedAt = const Value.absent()}) =>
      LocalCard(
        id: id ?? this.id,
        deckId: deckId ?? this.deckId,
        front: front ?? this.front,
        back: back ?? this.back,
        state: state ?? this.state,
        easeFactor: easeFactor ?? this.easeFactor,
        intervalDays: intervalDays ?? this.intervalDays,
        repetitions: repetitions ?? this.repetitions,
        dueAt: dueAt ?? this.dueAt,
        updatedAt: updatedAt ?? this.updatedAt,
        deletedAt: deletedAt.present ? deletedAt.value : this.deletedAt,
      );
  LocalCard copyWithCompanion(LocalCardsCompanion data) {
    return LocalCard(
      id: data.id.present ? data.id.value : this.id,
      deckId: data.deckId.present ? data.deckId.value : this.deckId,
      front: data.front.present ? data.front.value : this.front,
      back: data.back.present ? data.back.value : this.back,
      state: data.state.present ? data.state.value : this.state,
      easeFactor:
          data.easeFactor.present ? data.easeFactor.value : this.easeFactor,
      intervalDays: data.intervalDays.present
          ? data.intervalDays.value
          : this.intervalDays,
      repetitions:
          data.repetitions.present ? data.repetitions.value : this.repetitions,
      dueAt: data.dueAt.present ? data.dueAt.value : this.dueAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      deletedAt: data.deletedAt.present ? data.deletedAt.value : this.deletedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalCard(')
          ..write('id: $id, ')
          ..write('deckId: $deckId, ')
          ..write('front: $front, ')
          ..write('back: $back, ')
          ..write('state: $state, ')
          ..write('easeFactor: $easeFactor, ')
          ..write('intervalDays: $intervalDays, ')
          ..write('repetitions: $repetitions, ')
          ..write('dueAt: $dueAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, deckId, front, back, state, easeFactor,
      intervalDays, repetitions, dueAt, updatedAt, deletedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalCard &&
          other.id == this.id &&
          other.deckId == this.deckId &&
          other.front == this.front &&
          other.back == this.back &&
          other.state == this.state &&
          other.easeFactor == this.easeFactor &&
          other.intervalDays == this.intervalDays &&
          other.repetitions == this.repetitions &&
          other.dueAt == this.dueAt &&
          other.updatedAt == this.updatedAt &&
          other.deletedAt == this.deletedAt);
}

class LocalCardsCompanion extends UpdateCompanion<LocalCard> {
  final Value<String> id;
  final Value<String> deckId;
  final Value<String> front;
  final Value<String> back;
  final Value<String> state;
  final Value<double> easeFactor;
  final Value<int> intervalDays;
  final Value<int> repetitions;
  final Value<DateTime> dueAt;
  final Value<DateTime> updatedAt;
  final Value<DateTime?> deletedAt;
  final Value<int> rowid;
  const LocalCardsCompanion({
    this.id = const Value.absent(),
    this.deckId = const Value.absent(),
    this.front = const Value.absent(),
    this.back = const Value.absent(),
    this.state = const Value.absent(),
    this.easeFactor = const Value.absent(),
    this.intervalDays = const Value.absent(),
    this.repetitions = const Value.absent(),
    this.dueAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.deletedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalCardsCompanion.insert({
    required String id,
    required String deckId,
    required String front,
    required String back,
    required String state,
    required double easeFactor,
    required int intervalDays,
    required int repetitions,
    required DateTime dueAt,
    required DateTime updatedAt,
    this.deletedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        deckId = Value(deckId),
        front = Value(front),
        back = Value(back),
        state = Value(state),
        easeFactor = Value(easeFactor),
        intervalDays = Value(intervalDays),
        repetitions = Value(repetitions),
        dueAt = Value(dueAt),
        updatedAt = Value(updatedAt);
  static Insertable<LocalCard> custom({
    Expression<String>? id,
    Expression<String>? deckId,
    Expression<String>? front,
    Expression<String>? back,
    Expression<String>? state,
    Expression<double>? easeFactor,
    Expression<int>? intervalDays,
    Expression<int>? repetitions,
    Expression<int>? dueAt,
    Expression<int>? updatedAt,
    Expression<int>? deletedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (deckId != null) 'deck_id': deckId,
      if (front != null) 'front': front,
      if (back != null) 'back': back,
      if (state != null) 'state': state,
      if (easeFactor != null) 'ease_factor': easeFactor,
      if (intervalDays != null) 'interval_days': intervalDays,
      if (repetitions != null) 'repetitions': repetitions,
      if (dueAt != null) 'due_at': dueAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (deletedAt != null) 'deleted_at': deletedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalCardsCompanion copyWith(
      {Value<String>? id,
      Value<String>? deckId,
      Value<String>? front,
      Value<String>? back,
      Value<String>? state,
      Value<double>? easeFactor,
      Value<int>? intervalDays,
      Value<int>? repetitions,
      Value<DateTime>? dueAt,
      Value<DateTime>? updatedAt,
      Value<DateTime?>? deletedAt,
      Value<int>? rowid}) {
    return LocalCardsCompanion(
      id: id ?? this.id,
      deckId: deckId ?? this.deckId,
      front: front ?? this.front,
      back: back ?? this.back,
      state: state ?? this.state,
      easeFactor: easeFactor ?? this.easeFactor,
      intervalDays: intervalDays ?? this.intervalDays,
      repetitions: repetitions ?? this.repetitions,
      dueAt: dueAt ?? this.dueAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deletedAt: deletedAt ?? this.deletedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (deckId.present) {
      map['deck_id'] = Variable<String>(deckId.value);
    }
    if (front.present) {
      map['front'] = Variable<String>(front.value);
    }
    if (back.present) {
      map['back'] = Variable<String>(back.value);
    }
    if (state.present) {
      map['state'] = Variable<String>(state.value);
    }
    if (easeFactor.present) {
      map['ease_factor'] = Variable<double>(easeFactor.value);
    }
    if (intervalDays.present) {
      map['interval_days'] = Variable<int>(intervalDays.value);
    }
    if (repetitions.present) {
      map['repetitions'] = Variable<int>(repetitions.value);
    }
    if (dueAt.present) {
      map['due_at'] =
          Variable<int>($LocalCardsTable.$converterdueAt.toSql(dueAt.value));
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<int>(
          $LocalCardsTable.$converterupdatedAt.toSql(updatedAt.value));
    }
    if (deletedAt.present) {
      map['deleted_at'] = Variable<int>(
          $LocalCardsTable.$converterdeletedAtn.toSql(deletedAt.value));
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalCardsCompanion(')
          ..write('id: $id, ')
          ..write('deckId: $deckId, ')
          ..write('front: $front, ')
          ..write('back: $back, ')
          ..write('state: $state, ')
          ..write('easeFactor: $easeFactor, ')
          ..write('intervalDays: $intervalDays, ')
          ..write('repetitions: $repetitions, ')
          ..write('dueAt: $dueAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncEventsTable extends SyncEvents
    with TableInfo<$SyncEventsTable, SyncEvent> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _entityTypeMeta =
      const VerificationMeta('entityType');
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
      'entity_type', aliasedName, false,
      check: () => entityType.isIn(LocalEntityType.values),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _entityIdMeta =
      const VerificationMeta('entityId');
  @override
  late final GeneratedColumn<String> entityId = GeneratedColumn<String>(
      'entity_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _opMeta = const VerificationMeta('op');
  @override
  late final GeneratedColumn<String> op = GeneratedColumn<String>(
      'op', aliasedName, false,
      check: () => op.isIn(LocalSyncOp.values),
      type: DriftSqlType.string,
      requiredDuringInsert: true);
  static const VerificationMeta _payloadJsonMeta =
      const VerificationMeta('payloadJson');
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
      'payload_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  late final GeneratedColumnWithTypeConverter<DateTime, int> clientTs =
      GeneratedColumn<int>('client_ts', aliasedName, false,
              type: DriftSqlType.int, requiredDuringInsert: true)
          .withConverter<DateTime>($SyncEventsTable.$converterclientTs);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      check: () => status.isIn(LocalSyncStatus.values),
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(LocalSyncStatus.queued));
  static const VerificationMeta _retryCountMeta =
      const VerificationMeta('retryCount');
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
      'retry_count', aliasedName, false,
      check: () => ComparableExpr(retryCount).isBiggerOrEqualValue(0),
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  @override
  List<GeneratedColumn> get $columns =>
      [id, entityType, entityId, op, payloadJson, clientTs, status, retryCount];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_events';
  @override
  VerificationContext validateIntegrity(Insertable<SyncEvent> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('entity_type')) {
      context.handle(
          _entityTypeMeta,
          entityType.isAcceptableOrUnknown(
              data['entity_type']!, _entityTypeMeta));
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('entity_id')) {
      context.handle(_entityIdMeta,
          entityId.isAcceptableOrUnknown(data['entity_id']!, _entityIdMeta));
    } else if (isInserting) {
      context.missing(_entityIdMeta);
    }
    if (data.containsKey('op')) {
      context.handle(_opMeta, op.isAcceptableOrUnknown(data['op']!, _opMeta));
    } else if (isInserting) {
      context.missing(_opMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
          _payloadJsonMeta,
          payloadJson.isAcceptableOrUnknown(
              data['payload_json']!, _payloadJsonMeta));
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    }
    if (data.containsKey('retry_count')) {
      context.handle(
          _retryCountMeta,
          retryCount.isAcceptableOrUnknown(
              data['retry_count']!, _retryCountMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncEvent map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncEvent(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      entityType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}entity_type'])!,
      entityId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}entity_id'])!,
      op: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}op'])!,
      payloadJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload_json'])!,
      clientTs: $SyncEventsTable.$converterclientTs.fromSql(attachedDatabase
          .typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}client_ts'])!),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      retryCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}retry_count'])!,
    );
  }

  @override
  $SyncEventsTable createAlias(String alias) {
    return $SyncEventsTable(attachedDatabase, alias);
  }

  static TypeConverter<DateTime, int> $converterclientTs =
      const UtcDateTimeConverter();
}

class SyncEvent extends DataClass implements Insertable<SyncEvent> {
  final String id;
  final String entityType;
  final String entityId;
  final String op;
  final String payloadJson;
  final DateTime clientTs;
  final String status;
  final int retryCount;
  const SyncEvent(
      {required this.id,
      required this.entityType,
      required this.entityId,
      required this.op,
      required this.payloadJson,
      required this.clientTs,
      required this.status,
      required this.retryCount});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['entity_type'] = Variable<String>(entityType);
    map['entity_id'] = Variable<String>(entityId);
    map['op'] = Variable<String>(op);
    map['payload_json'] = Variable<String>(payloadJson);
    {
      map['client_ts'] =
          Variable<int>($SyncEventsTable.$converterclientTs.toSql(clientTs));
    }
    map['status'] = Variable<String>(status);
    map['retry_count'] = Variable<int>(retryCount);
    return map;
  }

  SyncEventsCompanion toCompanion(bool nullToAbsent) {
    return SyncEventsCompanion(
      id: Value(id),
      entityType: Value(entityType),
      entityId: Value(entityId),
      op: Value(op),
      payloadJson: Value(payloadJson),
      clientTs: Value(clientTs),
      status: Value(status),
      retryCount: Value(retryCount),
    );
  }

  factory SyncEvent.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncEvent(
      id: serializer.fromJson<String>(json['id']),
      entityType: serializer.fromJson<String>(json['entityType']),
      entityId: serializer.fromJson<String>(json['entityId']),
      op: serializer.fromJson<String>(json['op']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      clientTs: serializer.fromJson<DateTime>(json['clientTs']),
      status: serializer.fromJson<String>(json['status']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'entityType': serializer.toJson<String>(entityType),
      'entityId': serializer.toJson<String>(entityId),
      'op': serializer.toJson<String>(op),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'clientTs': serializer.toJson<DateTime>(clientTs),
      'status': serializer.toJson<String>(status),
      'retryCount': serializer.toJson<int>(retryCount),
    };
  }

  SyncEvent copyWith(
          {String? id,
          String? entityType,
          String? entityId,
          String? op,
          String? payloadJson,
          DateTime? clientTs,
          String? status,
          int? retryCount}) =>
      SyncEvent(
        id: id ?? this.id,
        entityType: entityType ?? this.entityType,
        entityId: entityId ?? this.entityId,
        op: op ?? this.op,
        payloadJson: payloadJson ?? this.payloadJson,
        clientTs: clientTs ?? this.clientTs,
        status: status ?? this.status,
        retryCount: retryCount ?? this.retryCount,
      );
  SyncEvent copyWithCompanion(SyncEventsCompanion data) {
    return SyncEvent(
      id: data.id.present ? data.id.value : this.id,
      entityType:
          data.entityType.present ? data.entityType.value : this.entityType,
      entityId: data.entityId.present ? data.entityId.value : this.entityId,
      op: data.op.present ? data.op.value : this.op,
      payloadJson:
          data.payloadJson.present ? data.payloadJson.value : this.payloadJson,
      clientTs: data.clientTs.present ? data.clientTs.value : this.clientTs,
      status: data.status.present ? data.status.value : this.status,
      retryCount:
          data.retryCount.present ? data.retryCount.value : this.retryCount,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncEvent(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('op: $op, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('clientTs: $clientTs, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, entityType, entityId, op, payloadJson, clientTs, status, retryCount);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncEvent &&
          other.id == this.id &&
          other.entityType == this.entityType &&
          other.entityId == this.entityId &&
          other.op == this.op &&
          other.payloadJson == this.payloadJson &&
          other.clientTs == this.clientTs &&
          other.status == this.status &&
          other.retryCount == this.retryCount);
}

class SyncEventsCompanion extends UpdateCompanion<SyncEvent> {
  final Value<String> id;
  final Value<String> entityType;
  final Value<String> entityId;
  final Value<String> op;
  final Value<String> payloadJson;
  final Value<DateTime> clientTs;
  final Value<String> status;
  final Value<int> retryCount;
  final Value<int> rowid;
  const SyncEventsCompanion({
    this.id = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityId = const Value.absent(),
    this.op = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.clientTs = const Value.absent(),
    this.status = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncEventsCompanion.insert({
    required String id,
    required String entityType,
    required String entityId,
    required String op,
    required String payloadJson,
    required DateTime clientTs,
    this.status = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        entityType = Value(entityType),
        entityId = Value(entityId),
        op = Value(op),
        payloadJson = Value(payloadJson),
        clientTs = Value(clientTs);
  static Insertable<SyncEvent> custom({
    Expression<String>? id,
    Expression<String>? entityType,
    Expression<String>? entityId,
    Expression<String>? op,
    Expression<String>? payloadJson,
    Expression<int>? clientTs,
    Expression<String>? status,
    Expression<int>? retryCount,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (entityType != null) 'entity_type': entityType,
      if (entityId != null) 'entity_id': entityId,
      if (op != null) 'op': op,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (clientTs != null) 'client_ts': clientTs,
      if (status != null) 'status': status,
      if (retryCount != null) 'retry_count': retryCount,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncEventsCompanion copyWith(
      {Value<String>? id,
      Value<String>? entityType,
      Value<String>? entityId,
      Value<String>? op,
      Value<String>? payloadJson,
      Value<DateTime>? clientTs,
      Value<String>? status,
      Value<int>? retryCount,
      Value<int>? rowid}) {
    return SyncEventsCompanion(
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      op: op ?? this.op,
      payloadJson: payloadJson ?? this.payloadJson,
      clientTs: clientTs ?? this.clientTs,
      status: status ?? this.status,
      retryCount: retryCount ?? this.retryCount,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityId.present) {
      map['entity_id'] = Variable<String>(entityId.value);
    }
    if (op.present) {
      map['op'] = Variable<String>(op.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (clientTs.present) {
      map['client_ts'] = Variable<int>(
          $SyncEventsTable.$converterclientTs.toSql(clientTs.value));
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncEventsCompanion(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('op: $op, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('clientTs: $clientTs, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $LocalDecksTable localDecks = $LocalDecksTable(this);
  late final $LocalCardsTable localCards = $LocalCardsTable(this);
  late final $SyncEventsTable syncEvents = $SyncEventsTable(this);
  late final LocalDeckDao localDeckDao = LocalDeckDao(this as AppDatabase);
  late final LocalCardDao localCardDao = LocalCardDao(this as AppDatabase);
  late final LocalSyncEventDao localSyncEventDao =
      LocalSyncEventDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [localDecks, localCards, syncEvents];
}

typedef $$LocalDecksTableCreateCompanionBuilder = LocalDecksCompanion Function({
  required String id,
  required String name,
  required String description,
  required bool isPublic,
  required DateTime updatedAt,
  Value<DateTime?> deletedAt,
  Value<int> rowid,
});
typedef $$LocalDecksTableUpdateCompanionBuilder = LocalDecksCompanion Function({
  Value<String> id,
  Value<String> name,
  Value<String> description,
  Value<bool> isPublic,
  Value<DateTime> updatedAt,
  Value<DateTime?> deletedAt,
  Value<int> rowid,
});

class $$LocalDecksTableFilterComposer
    extends Composer<_$AppDatabase, $LocalDecksTable> {
  $$LocalDecksTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get isPublic => $composableBuilder(
      column: $table.isPublic, builder: (column) => ColumnFilters(column));

  ColumnWithTypeConverterFilters<DateTime, DateTime, int> get updatedAt =>
      $composableBuilder(
          column: $table.updatedAt,
          builder: (column) => ColumnWithTypeConverterFilters(column));

  ColumnWithTypeConverterFilters<DateTime?, DateTime, int> get deletedAt =>
      $composableBuilder(
          column: $table.deletedAt,
          builder: (column) => ColumnWithTypeConverterFilters(column));
}

class $$LocalDecksTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalDecksTable> {
  $$LocalDecksTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get name => $composableBuilder(
      column: $table.name, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get isPublic => $composableBuilder(
      column: $table.isPublic, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get updatedAt => $composableBuilder(
      column: $table.updatedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get deletedAt => $composableBuilder(
      column: $table.deletedAt, builder: (column) => ColumnOrderings(column));
}

class $$LocalDecksTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalDecksTable> {
  $$LocalDecksTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<bool> get isPublic =>
      $composableBuilder(column: $table.isPublic, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime, int> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime?, int> get deletedAt =>
      $composableBuilder(column: $table.deletedAt, builder: (column) => column);
}

class $$LocalDecksTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalDecksTable,
    LocalDeck,
    $$LocalDecksTableFilterComposer,
    $$LocalDecksTableOrderingComposer,
    $$LocalDecksTableAnnotationComposer,
    $$LocalDecksTableCreateCompanionBuilder,
    $$LocalDecksTableUpdateCompanionBuilder,
    (LocalDeck, BaseReferences<_$AppDatabase, $LocalDecksTable, LocalDeck>),
    LocalDeck,
    PrefetchHooks Function()> {
  $$LocalDecksTableTableManager(_$AppDatabase db, $LocalDecksTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalDecksTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalDecksTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalDecksTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> name = const Value.absent(),
            Value<String> description = const Value.absent(),
            Value<bool> isPublic = const Value.absent(),
            Value<DateTime> updatedAt = const Value.absent(),
            Value<DateTime?> deletedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalDecksCompanion(
            id: id,
            name: name,
            description: description,
            isPublic: isPublic,
            updatedAt: updatedAt,
            deletedAt: deletedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String name,
            required String description,
            required bool isPublic,
            required DateTime updatedAt,
            Value<DateTime?> deletedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalDecksCompanion.insert(
            id: id,
            name: name,
            description: description,
            isPublic: isPublic,
            updatedAt: updatedAt,
            deletedAt: deletedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalDecksTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $LocalDecksTable,
    LocalDeck,
    $$LocalDecksTableFilterComposer,
    $$LocalDecksTableOrderingComposer,
    $$LocalDecksTableAnnotationComposer,
    $$LocalDecksTableCreateCompanionBuilder,
    $$LocalDecksTableUpdateCompanionBuilder,
    (LocalDeck, BaseReferences<_$AppDatabase, $LocalDecksTable, LocalDeck>),
    LocalDeck,
    PrefetchHooks Function()>;
typedef $$LocalCardsTableCreateCompanionBuilder = LocalCardsCompanion Function({
  required String id,
  required String deckId,
  required String front,
  required String back,
  required String state,
  required double easeFactor,
  required int intervalDays,
  required int repetitions,
  required DateTime dueAt,
  required DateTime updatedAt,
  Value<DateTime?> deletedAt,
  Value<int> rowid,
});
typedef $$LocalCardsTableUpdateCompanionBuilder = LocalCardsCompanion Function({
  Value<String> id,
  Value<String> deckId,
  Value<String> front,
  Value<String> back,
  Value<String> state,
  Value<double> easeFactor,
  Value<int> intervalDays,
  Value<int> repetitions,
  Value<DateTime> dueAt,
  Value<DateTime> updatedAt,
  Value<DateTime?> deletedAt,
  Value<int> rowid,
});

class $$LocalCardsTableFilterComposer
    extends Composer<_$AppDatabase, $LocalCardsTable> {
  $$LocalCardsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get deckId => $composableBuilder(
      column: $table.deckId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get front => $composableBuilder(
      column: $table.front, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get back => $composableBuilder(
      column: $table.back, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get state => $composableBuilder(
      column: $table.state, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get easeFactor => $composableBuilder(
      column: $table.easeFactor, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get repetitions => $composableBuilder(
      column: $table.repetitions, builder: (column) => ColumnFilters(column));

  ColumnWithTypeConverterFilters<DateTime, DateTime, int> get dueAt =>
      $composableBuilder(
          column: $table.dueAt,
          builder: (column) => ColumnWithTypeConverterFilters(column));

  ColumnWithTypeConverterFilters<DateTime, DateTime, int> get updatedAt =>
      $composableBuilder(
          column: $table.updatedAt,
          builder: (column) => ColumnWithTypeConverterFilters(column));

  ColumnWithTypeConverterFilters<DateTime?, DateTime, int> get deletedAt =>
      $composableBuilder(
          column: $table.deletedAt,
          builder: (column) => ColumnWithTypeConverterFilters(column));
}

class $$LocalCardsTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalCardsTable> {
  $$LocalCardsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get deckId => $composableBuilder(
      column: $table.deckId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get front => $composableBuilder(
      column: $table.front, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get back => $composableBuilder(
      column: $table.back, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get state => $composableBuilder(
      column: $table.state, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get easeFactor => $composableBuilder(
      column: $table.easeFactor, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get repetitions => $composableBuilder(
      column: $table.repetitions, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get dueAt => $composableBuilder(
      column: $table.dueAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get updatedAt => $composableBuilder(
      column: $table.updatedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get deletedAt => $composableBuilder(
      column: $table.deletedAt, builder: (column) => ColumnOrderings(column));
}

class $$LocalCardsTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalCardsTable> {
  $$LocalCardsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get deckId =>
      $composableBuilder(column: $table.deckId, builder: (column) => column);

  GeneratedColumn<String> get front =>
      $composableBuilder(column: $table.front, builder: (column) => column);

  GeneratedColumn<String> get back =>
      $composableBuilder(column: $table.back, builder: (column) => column);

  GeneratedColumn<String> get state =>
      $composableBuilder(column: $table.state, builder: (column) => column);

  GeneratedColumn<double> get easeFactor => $composableBuilder(
      column: $table.easeFactor, builder: (column) => column);

  GeneratedColumn<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays, builder: (column) => column);

  GeneratedColumn<int> get repetitions => $composableBuilder(
      column: $table.repetitions, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime, int> get dueAt =>
      $composableBuilder(column: $table.dueAt, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime, int> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime?, int> get deletedAt =>
      $composableBuilder(column: $table.deletedAt, builder: (column) => column);
}

class $$LocalCardsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $LocalCardsTable,
    LocalCard,
    $$LocalCardsTableFilterComposer,
    $$LocalCardsTableOrderingComposer,
    $$LocalCardsTableAnnotationComposer,
    $$LocalCardsTableCreateCompanionBuilder,
    $$LocalCardsTableUpdateCompanionBuilder,
    (LocalCard, BaseReferences<_$AppDatabase, $LocalCardsTable, LocalCard>),
    LocalCard,
    PrefetchHooks Function()> {
  $$LocalCardsTableTableManager(_$AppDatabase db, $LocalCardsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalCardsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalCardsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalCardsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> deckId = const Value.absent(),
            Value<String> front = const Value.absent(),
            Value<String> back = const Value.absent(),
            Value<String> state = const Value.absent(),
            Value<double> easeFactor = const Value.absent(),
            Value<int> intervalDays = const Value.absent(),
            Value<int> repetitions = const Value.absent(),
            Value<DateTime> dueAt = const Value.absent(),
            Value<DateTime> updatedAt = const Value.absent(),
            Value<DateTime?> deletedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalCardsCompanion(
            id: id,
            deckId: deckId,
            front: front,
            back: back,
            state: state,
            easeFactor: easeFactor,
            intervalDays: intervalDays,
            repetitions: repetitions,
            dueAt: dueAt,
            updatedAt: updatedAt,
            deletedAt: deletedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String deckId,
            required String front,
            required String back,
            required String state,
            required double easeFactor,
            required int intervalDays,
            required int repetitions,
            required DateTime dueAt,
            required DateTime updatedAt,
            Value<DateTime?> deletedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              LocalCardsCompanion.insert(
            id: id,
            deckId: deckId,
            front: front,
            back: back,
            state: state,
            easeFactor: easeFactor,
            intervalDays: intervalDays,
            repetitions: repetitions,
            dueAt: dueAt,
            updatedAt: updatedAt,
            deletedAt: deletedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalCardsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $LocalCardsTable,
    LocalCard,
    $$LocalCardsTableFilterComposer,
    $$LocalCardsTableOrderingComposer,
    $$LocalCardsTableAnnotationComposer,
    $$LocalCardsTableCreateCompanionBuilder,
    $$LocalCardsTableUpdateCompanionBuilder,
    (LocalCard, BaseReferences<_$AppDatabase, $LocalCardsTable, LocalCard>),
    LocalCard,
    PrefetchHooks Function()>;
typedef $$SyncEventsTableCreateCompanionBuilder = SyncEventsCompanion Function({
  required String id,
  required String entityType,
  required String entityId,
  required String op,
  required String payloadJson,
  required DateTime clientTs,
  Value<String> status,
  Value<int> retryCount,
  Value<int> rowid,
});
typedef $$SyncEventsTableUpdateCompanionBuilder = SyncEventsCompanion Function({
  Value<String> id,
  Value<String> entityType,
  Value<String> entityId,
  Value<String> op,
  Value<String> payloadJson,
  Value<DateTime> clientTs,
  Value<String> status,
  Value<int> retryCount,
  Value<int> rowid,
});

class $$SyncEventsTableFilterComposer
    extends Composer<_$AppDatabase, $SyncEventsTable> {
  $$SyncEventsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get entityId => $composableBuilder(
      column: $table.entityId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get op => $composableBuilder(
      column: $table.op, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnFilters(column));

  ColumnWithTypeConverterFilters<DateTime, DateTime, int> get clientTs =>
      $composableBuilder(
          column: $table.clientTs,
          builder: (column) => ColumnWithTypeConverterFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => ColumnFilters(column));
}

class $$SyncEventsTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncEventsTable> {
  $$SyncEventsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get entityId => $composableBuilder(
      column: $table.entityId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get op => $composableBuilder(
      column: $table.op, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get clientTs => $composableBuilder(
      column: $table.clientTs, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => ColumnOrderings(column));
}

class $$SyncEventsTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncEventsTable> {
  $$SyncEventsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => column);

  GeneratedColumn<String> get entityId =>
      $composableBuilder(column: $table.entityId, builder: (column) => column);

  GeneratedColumn<String> get op =>
      $composableBuilder(column: $table.op, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => column);

  GeneratedColumnWithTypeConverter<DateTime, int> get clientTs =>
      $composableBuilder(column: $table.clientTs, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => column);
}

class $$SyncEventsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $SyncEventsTable,
    SyncEvent,
    $$SyncEventsTableFilterComposer,
    $$SyncEventsTableOrderingComposer,
    $$SyncEventsTableAnnotationComposer,
    $$SyncEventsTableCreateCompanionBuilder,
    $$SyncEventsTableUpdateCompanionBuilder,
    (SyncEvent, BaseReferences<_$AppDatabase, $SyncEventsTable, SyncEvent>),
    SyncEvent,
    PrefetchHooks Function()> {
  $$SyncEventsTableTableManager(_$AppDatabase db, $SyncEventsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncEventsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncEventsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncEventsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> entityType = const Value.absent(),
            Value<String> entityId = const Value.absent(),
            Value<String> op = const Value.absent(),
            Value<String> payloadJson = const Value.absent(),
            Value<DateTime> clientTs = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<int> retryCount = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SyncEventsCompanion(
            id: id,
            entityType: entityType,
            entityId: entityId,
            op: op,
            payloadJson: payloadJson,
            clientTs: clientTs,
            status: status,
            retryCount: retryCount,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String entityType,
            required String entityId,
            required String op,
            required String payloadJson,
            required DateTime clientTs,
            Value<String> status = const Value.absent(),
            Value<int> retryCount = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SyncEventsCompanion.insert(
            id: id,
            entityType: entityType,
            entityId: entityId,
            op: op,
            payloadJson: payloadJson,
            clientTs: clientTs,
            status: status,
            retryCount: retryCount,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$SyncEventsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $SyncEventsTable,
    SyncEvent,
    $$SyncEventsTableFilterComposer,
    $$SyncEventsTableOrderingComposer,
    $$SyncEventsTableAnnotationComposer,
    $$SyncEventsTableCreateCompanionBuilder,
    $$SyncEventsTableUpdateCompanionBuilder,
    (SyncEvent, BaseReferences<_$AppDatabase, $SyncEventsTable, SyncEvent>),
    SyncEvent,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$LocalDecksTableTableManager get localDecks =>
      $$LocalDecksTableTableManager(_db, _db.localDecks);
  $$LocalCardsTableTableManager get localCards =>
      $$LocalCardsTableTableManager(_db, _db.localCards);
  $$SyncEventsTableTableManager get syncEvents =>
      $$SyncEventsTableTableManager(_db, _db.syncEvents);
}

mixin _$LocalDeckDaoMixin on DatabaseAccessor<AppDatabase> {
  $LocalDecksTable get localDecks => attachedDatabase.localDecks;
  LocalDeckDaoManager get managers => LocalDeckDaoManager(this);
}

class LocalDeckDaoManager {
  final _$LocalDeckDaoMixin _db;
  LocalDeckDaoManager(this._db);
  $$LocalDecksTableTableManager get localDecks =>
      $$LocalDecksTableTableManager(_db.attachedDatabase, _db.localDecks);
}

mixin _$LocalCardDaoMixin on DatabaseAccessor<AppDatabase> {
  $LocalCardsTable get localCards => attachedDatabase.localCards;
  LocalCardDaoManager get managers => LocalCardDaoManager(this);
}

class LocalCardDaoManager {
  final _$LocalCardDaoMixin _db;
  LocalCardDaoManager(this._db);
  $$LocalCardsTableTableManager get localCards =>
      $$LocalCardsTableTableManager(_db.attachedDatabase, _db.localCards);
}

mixin _$LocalSyncEventDaoMixin on DatabaseAccessor<AppDatabase> {
  $SyncEventsTable get syncEvents => attachedDatabase.syncEvents;
  LocalSyncEventDaoManager get managers => LocalSyncEventDaoManager(this);
}

class LocalSyncEventDaoManager {
  final _$LocalSyncEventDaoMixin _db;
  LocalSyncEventDaoManager(this._db);
  $$SyncEventsTableTableManager get syncEvents =>
      $$SyncEventsTableTableManager(_db.attachedDatabase, _db.syncEvents);
}
