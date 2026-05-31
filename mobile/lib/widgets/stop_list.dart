import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/models.dart';
import '../providers/app_providers.dart';

class StopListSliver extends ConsumerWidget {
  const StopListSliver({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stops = ref.watch(stopsProvider);

    if (stops.isEmpty) {
      return const SliverToBoxAdapter(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text(
            'Search above or tap the map to add stops. No route until you optimize.',
            style: TextStyle(color: Colors.black54),
          ),
        ),
      );
    }

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) {
          final stop = stops[index];
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (index > 0) const Divider(height: 1),
              StopListTile(index: index, stop: stop),
            ],
          );
        },
        childCount: stops.length,
      ),
    );
  }
}

class StopListTile extends ConsumerWidget {
  const StopListTile({
    super.key,
    required this.index,
    required this.stop,
  });

  final int index;
  final StopDto stop;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListTile(
      dense: true,
      visualDensity: VisualDensity.compact,
      leading: Icon(Icons.place_outlined, color: Colors.grey.shade600, size: 20),
      title: TextFormField(
        key: ValueKey('stop-name-$index-${stop.lat}-${stop.lng}'),
        initialValue: stop.name,
        decoration: const InputDecoration(
          isDense: true,
          border: InputBorder.none,
          hintText: 'Stop name',
          contentPadding: EdgeInsets.zero,
        ),
        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
        onChanged: (value) {
          ref.read(stopsProvider.notifier).updateName(index, value);
        },
      ),
      subtitle: Text(
        '${stop.lat.toStringAsFixed(5)}, ${stop.lng.toStringAsFixed(5)}',
        style: const TextStyle(fontSize: 11),
      ),
      trailing: IconButton(
        icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
        onPressed: () {
          ref.read(stopsProvider.notifier).removeAt(index);
          ref.read(routeOrderProvider.notifier).state = null;
          ref.read(orderedStopsProvider.notifier).state = null;
        },
      ),
    );
  }
}
