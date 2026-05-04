import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/features/cards/providers/cards_providers.dart';

class DeckListTile extends ConsumerWidget {
  const DeckListTile({
    super.key,
    required this.deck,
    this.onTap,
  });

  final LocalDeck deck;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final hasDescription = deck.description.trim().isNotEmpty;
    final cardsAsync = ref.watch(cardsForDeckStreamProvider(deck.id));
    final dueAsync = ref.watch(dueCardCountProvider(deck.id));

    final countLabel = cardsAsync.when(
      loading: () => '— cards',
      error: (_, __) => '— cards',
      data: (cards) {
        final n = cards.length;
        return n == 1 ? '1 card' : '$n cards';
      },
    );

    final dueCount = dueAsync.valueOrNull ?? 0;

    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: Colors.white12),
      ),
      clipBehavior: Clip.antiAlias,
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 8,
        ),
        title: Text(
          deck.name,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        subtitle: hasDescription
            ? Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  deck.description,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              )
            : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  countLabel,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                if (dueCount > 0) ...[
                  const SizedBox(height: 2),
                  Text(
                    dueCount == 1 ? '1 devido' : '$dueCount devidos',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: const Color(0xFFFBBF24), // amber, igual badge LEARNING
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(width: 6),
            Icon(
              Icons.chevron_right,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ],
        ),
      ),
    );
  }
}
