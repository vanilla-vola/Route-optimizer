import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/solver_models.dart';
import '../models/transport_modes.dart';
import '../providers/app_providers.dart';

class TransportModeBar extends ConsumerWidget {
  const TransportModeBar({super.key, this.availableModeIds});

  final List<String>? availableModeIds;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(transportModeProvider);
    final colorScheme = Theme.of(context).colorScheme;
    final allowed = availableModeIds ?? allTransportModeIds;
    final modes = TransportModeOption.all
        .where((mode) => allowed.contains(mode.id))
        .toList();

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          for (final mode in modes)
            _ModeButton(
              mode: mode,
              selected: selected == mode.id,
              colorScheme: colorScheme,
              onTap: () {
                ref.read(transportModeProvider.notifier).state = mode.id;
              },
            ),
        ],
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  const _ModeButton({
    required this.mode,
    required this.selected,
    required this.colorScheme,
    required this.onTap,
  });

  final TransportModeOption mode;
  final bool selected;
  final ColorScheme colorScheme;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: mode.label,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? colorScheme.primaryContainer : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? colorScheme.primary : colorScheme.outlineVariant,
            ),
          ),
          child: Icon(
            mode.icon,
            size: 22,
            color: selected ? colorScheme.primary : colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
