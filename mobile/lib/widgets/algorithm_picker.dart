import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/app_providers.dart';

class AlgorithmPicker extends ConsumerWidget {
  const AlgorithmPicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupsAsync = ref.watch(solverGroupsProvider);
    final selectedId = ref.watch(selectedSolverProvider);
    final apiOnline = ref.watch(apiOnlineProvider).value ?? true;

    return groupsAsync.when(
      data: (groups) {
        final options = [
          for (final group in groups) ...group.options,
        ];
        if (options.isEmpty) {
          return const SizedBox(
            width: 160,
            child: Text(
              'No algorithms',
              style: TextStyle(fontSize: 12),
            ),
          );
        }

        return SizedBox(
          width: 220,
          child: DropdownButtonFormField<String>(
            isExpanded: true,
            value: options.any((option) => option.id == selectedId)
                ? selectedId
                : options.first.id,
            decoration: const InputDecoration(
              labelText: 'Algorithm',
              isDense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              border: OutlineInputBorder(),
            ),
            items: [
              for (final group in groups) ...[
                DropdownMenuItem<String>(
                  enabled: false,
                  value: '__group__${group.label}',
                  child: Text(
                    group.label,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ),
                ...group.options.map(
                  (option) => DropdownMenuItem<String>(
                    value: option.id,
                    child: Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: Text(
                        option.label,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 13),
                      ),
                    ),
                  ),
                ),
              ],
            ],
            onChanged: apiOnline
                ? (value) {
                    if (value == null || value == selectedId) return;
                    ref.read(selectedSolverProvider.notifier).state = value;
                  }
                : null,
          ),
        );
      },
      loading: () => const SizedBox(
        width: 18,
        height: 18,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
      error: (error, stackTrace) => const SizedBox(
        width: 160,
        child: Text(
          'Algorithms unavailable',
          style: TextStyle(fontSize: 12),
        ),
      ),
    );
  }
}
