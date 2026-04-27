import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/core/db/tables.dart';
import 'package:synapse_mobile/core/providers.dart';
import 'package:synapse_mobile/core/srs/sm2.dart';
import 'package:uuid/uuid.dart';

class ReviewScreen extends ConsumerStatefulWidget {
  const ReviewScreen({
    required this.deckId,
    this.deckName,
    super.key,
  });

  final String deckId;
  final String? deckName;

  @override
  ConsumerState<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends ConsumerState<ReviewScreen> {
  static final _uuid = Uuid();

  var _cards = <LocalCard>[];
  var _currentIndex = 0;
  var _isLoading = true;
  var _isSubmitting = false;
  var _showAnswer = false;
  DateTime? _cardStartedAt;
  Object? _loadError;

  @override
  void initState() {
    super.initState();
    _loadDueCards();
  }

  Future<void> _loadDueCards() async {
    setState(() {
      _isLoading = true;
      _loadError = null;
    });

    try {
      final database = ref.read(appDatabaseProvider);
      final dueCards = await database.localCardDao.getDueCards(
        nowUtc: DateTime.now().toUtc(),
        limit: 500,
      );

      if (!mounted) {
        return;
      }
      setState(() {
        _cards = dueCards
            .where((card) => card.deckId == widget.deckId)
            .toList(growable: false);
        _currentIndex = 0;
        _showAnswer = false;
        _cardStartedAt = DateTime.now().toUtc();
        _isLoading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loadError = error;
        _isLoading = false;
      });
    }
  }

  Future<void> _submitRating(String rating) async {
    if (_isSubmitting || _currentCard == null) {
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    try {
      final card = _currentCard!;
      final nowUtc = DateTime.now().toUtc();
      final startedAt = _cardStartedAt ?? nowUtc;
      final durationMs = nowUtc.difference(startedAt).inMilliseconds;
      final nextState = calculateNextState(
        state: card.state,
        easeFactor: card.easeFactor,
        intervalDays: card.intervalDays,
        repetitions: card.repetitions,
        rating: rating,
      );
      final intervalDays = nextState['interval_days']! as int;
      final updatedCard = LocalCardsCompanion(
        id: Value(card.id),
        deckId: Value(card.deckId),
        front: Value(card.front),
        back: Value(card.back),
        state: Value(nextState['state']! as String),
        easeFactor: Value(nextState['ease_factor']! as double),
        intervalDays: Value(intervalDays),
        repetitions: Value(nextState['repetitions']! as int),
        dueAt: Value(nowUtc.add(Duration(days: intervalDays))),
        updatedAt: Value(nowUtc),
        deletedAt: Value(card.deletedAt),
      );
      final syncEvent = SyncEventsCompanion(
        id: Value(_uuid.v4()),
        entityType: const Value(LocalEntityType.card),
        entityId: Value(card.id),
        op: const Value(LocalSyncOp.review),
        payloadJson: Value(
          jsonEncode({
            'rating': rating,
            'duration_ms': durationMs < 0 ? 0 : durationMs,
          }),
        ),
        clientTs: Value(nowUtc),
        status: const Value(LocalSyncStatus.queued),
      );

      final database = ref.read(appDatabaseProvider);
      await database.transaction(() async {
        await database.localCardDao.upsertCard(updatedCard);
        await database.localSyncEventDao.enqueue(syncEvent);
      });

      if (!mounted) {
        return;
      }
      setState(() {
        _cards = [
          ..._cards.take(_currentIndex),
          ..._cards.skip(_currentIndex + 1),
        ];
        if (_currentIndex >= _cards.length && _currentIndex > 0) {
          _currentIndex -= 1;
        }
        _showAnswer = false;
        _cardStartedAt = DateTime.now().toUtc();
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erro ao salvar revisao: $error')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  LocalCard? get _currentCard {
    if (_currentIndex < 0 || _currentIndex >= _cards.length) {
      return null;
    }
    return _cards[_currentIndex];
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.deckName ?? 'Revisao';

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            onPressed: _isLoading ? null : _loadDueCards,
            icon: const Icon(Icons.refresh),
            tooltip: 'Atualizar',
          ),
        ],
      ),
      body: _buildBody(context),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_loadError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Erro ao carregar revisoes: $_loadError',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _loadDueCards,
                icon: const Icon(Icons.refresh),
                label: const Text('Tentar novamente'),
              ),
            ],
          ),
        ),
      );
    }

    final card = _currentCard;
    if (card == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle_outline, size: 48),
              const SizedBox(height: 16),
              const Text(
                'Tudo revisado por agora.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _loadDueCards,
                icon: const Icon(Icons.refresh),
                label: const Text('Atualizar'),
              ),
            ],
          ),
        ),
      );
    }

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              '${_currentIndex + 1} de ${_cards.length}',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Center(
                child: SingleChildScrollView(
                  child: Text(
                    _showAnswer ? card.back : card.front,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            if (!_showAnswer)
              FilledButton(
                onPressed: () {
                  setState(() {
                    _showAnswer = true;
                  });
                },
                child: const Text('Mostrar Resposta'),
              )
            else
              _RatingButtons(
                isSubmitting: _isSubmitting,
                onRating: _submitRating,
              ),
          ],
        ),
      ),
    );
  }
}

class _RatingButtons extends StatelessWidget {
  const _RatingButtons({
    required this.isSubmitting,
    required this.onRating,
  });

  final bool isSubmitting;
  final ValueChanged<String> onRating;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: 8,
      runSpacing: 8,
      children: [
        _RatingButton(
          label: 'Again',
          rating: 'again',
          isSubmitting: isSubmitting,
          onRating: onRating,
        ),
        _RatingButton(
          label: 'Hard',
          rating: 'hard',
          isSubmitting: isSubmitting,
          onRating: onRating,
        ),
        _RatingButton(
          label: 'Good',
          rating: 'good',
          isSubmitting: isSubmitting,
          onRating: onRating,
        ),
        _RatingButton(
          label: 'Easy',
          rating: 'easy',
          isSubmitting: isSubmitting,
          onRating: onRating,
        ),
      ],
    );
  }
}

class _RatingButton extends StatelessWidget {
  const _RatingButton({
    required this.label,
    required this.rating,
    required this.isSubmitting,
    required this.onRating,
  });

  final String label;
  final String rating;
  final bool isSubmitting;
  final ValueChanged<String> onRating;

  @override
  Widget build(BuildContext context) {
    return FilledButton(
      onPressed: isSubmitting ? null : () => onRating(rating),
      child: Text(label),
    );
  }
}
