import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/core/providers.dart';
import 'package:synapse_mobile/features/review/review_screen.dart';

final decksProvider = StreamProvider.autoDispose<List<LocalDeck>>((ref) {
  final database = ref.watch(appDatabaseProvider);
  return database.localDeckDao.watchDecks();
});

class DecksScreen extends ConsumerStatefulWidget {
  const DecksScreen({super.key});

  @override
  ConsumerState<DecksScreen> createState() => _DecksScreenState();
}

class _DecksScreenState extends ConsumerState<DecksScreen> {
  bool _isSyncing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _syncNow(showSuccess: false, offlineMessage: true);
      }
    });
  }

  Future<void> _syncNow({
    bool showSuccess = true,
    bool offlineMessage = false,
  }) async {
    if (_isSyncing) {
      return;
    }

    setState(() {
      _isSyncing = true;
    });

    try {
      final syncService = ref.read(syncServiceProvider);
      await syncService.pushPendingEvents();

      var pullResult = await syncService.pullChanges();
      while (pullResult.hasMore && pullResult.nextCursor != null) {
        pullResult = await syncService.pullChanges(
          cursor: pullResult.nextCursor,
        );
      }

      if (!mounted) {
        return;
      }
      if (showSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sync concluido.')),
        );
      }
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            offlineMessage
                ? 'Modo offline ativo. A sincronizacao sera tentada depois.'
                : 'Falha ao sincronizar: $error',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSyncing = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final decks = ref.watch(decksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Synapse'),
        actions: [
          TextButton.icon(
            onPressed: _isSyncing ? null : _syncNow,
            icon: _isSyncing
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.sync),
            label: const Text('Sync Now'),
          ),
        ],
      ),
      body: decks.when(
        data: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Text('Nenhum deck disponivel. Sincronize para comecar.'),
            );
          }

          return ListView.separated(
            itemCount: items.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final deck = items[index];
              return ListTile(
                title: Text(deck.name),
                subtitle: deck.description.isEmpty
                    ? null
                    : Text(
                        deck.description,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => ReviewScreen(
                        deckId: deck.id,
                        deckName: deck.name,
                      ),
                    ),
                  );
                },
              );
            },
          );
        },
        error: (error, _) => Center(
          child: Text('Erro ao carregar decks: $error'),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}
