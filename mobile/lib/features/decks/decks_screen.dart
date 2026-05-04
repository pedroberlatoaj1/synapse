import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/providers.dart';
import 'package:synapse_mobile/features/decks/providers/decks_providers.dart';
import 'package:synapse_mobile/features/decks/widgets/create_deck_dialog.dart';
import 'package:synapse_mobile/features/decks/widgets/deck_list_tile.dart';
import 'package:synapse_mobile/features/decks/widgets/empty_decks_view.dart';
import 'package:synapse_mobile/features/cards/screens/deck_detail_screen.dart';

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
    if (_isSyncing) return;
    setState(() => _isSyncing = true);

    final messenger = ScaffoldMessenger.of(context);

    try {
      final syncService = ref.read(syncServiceProvider);
      await syncService.pushPendingEvents();

      var pullResult = await syncService.pullChanges();
      while (pullResult.hasMore && pullResult.nextCursor != null) {
        pullResult = await syncService.pullChanges(
          cursor: pullResult.nextCursor,
        );
      }

      if (!mounted) return;
      if (showSuccess) {
        messenger.showSnackBar(
          const SnackBar(content: Text('Sync concluído.')),
        );
      }
    } catch (error) {
      if (!mounted) return;
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            offlineMessage
                ? 'Modo offline ativo. A sincronização será tentada depois.'
                : 'Falha ao sincronizar: $error',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSyncing = false);
      }
    }
  }

  Future<void> _openCreateDialog() {
    return showDialog<void>(
      context: context,
      builder: (_) => const CreateDeckDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final decksAsync = ref.watch(decksStreamProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Meus Decks'),
        centerTitle: false,
        actions: [
          IconButton(
            tooltip: 'Sincronizar',
            onPressed: _isSyncing ? null : () => _syncNow(),
            icon: _isSyncing
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.sync),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openCreateDialog,
        icon: const Icon(Icons.add),
        label: const Text('Novo Deck'),
      ),
      body: decksAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Erro ao carregar decks',
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              FilledButton.tonal(
                onPressed: () => ref.invalidate(decksStreamProvider),
                child: const Text('Tentar novamente'),
              ),
            ],
          ),
        ),
        data: (decks) {
          if (decks.isEmpty) {
            return EmptyDecksView(onCreate: _openCreateDialog);
          }

          return ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 8) +
                const EdgeInsets.only(bottom: 88),
            itemCount: decks.length,
            itemBuilder: (context, index) {
              final deck = decks[index];
              return DeckListTile(
                deck: deck,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => DeckDetailScreen(deck: deck),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
