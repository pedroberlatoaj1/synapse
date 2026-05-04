import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/core/providers.dart';
import 'package:synapse_mobile/features/decks/data/deck_repository.dart';

final deckRepositoryProvider = Provider<DeckRepository>((ref) {
  return DeckRepository(ref.watch(appDatabaseProvider));
});

final decksStreamProvider =
    StreamProvider.autoDispose<List<LocalDeck>>((ref) {
  return ref.watch(deckRepositoryProvider).watchDecks();
});
