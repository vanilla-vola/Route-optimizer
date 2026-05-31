import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../models/models.dart';
import '../providers/app_providers.dart';

class InstancePicker extends ConsumerWidget {
  const InstancePicker({super.key});

  Future<void> _openPicker(BuildContext context, WidgetRef ref) async {
    final instances = await ref.read(benchmarkInstancesProvider.future);

    if (!context.mounted) return;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) {
        return _InstancePickerSheet(
          instances: instances,
          onLoad: (detail) {
            ref.read(selectedBenchmarkInstanceProvider.notifier).state =
                detail.id;
            ref.read(stopsProvider.notifier).setAll(detail.stops);
            ref.read(roundTripProvider.notifier).state = detail.roundTrip;
            ref.read(transportModeProvider.notifier).state = detail.mode;
            ref.read(routeOrderProvider.notifier).state = null;
            ref.read(orderedStopsProvider.notifier).state = null;
            ref.read(benchmarkCacheProvider.notifier).state = null;
            ref.read(compareCacheProvider.notifier).state = null;
            if (detail.stops.isNotEmpty) {
              final first = detail.stops.first;
              ref.read(mapFocusProvider.notifier).state =
                  LatLng(first.lat, first.lng);
            }
            Navigator.of(sheetContext).pop();
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedBenchmarkInstanceProvider);
    final instancesAsync = ref.watch(benchmarkInstancesProvider);

    return instancesAsync.when(
      data: (instances) {
        BenchmarkInstanceSummaryDto? summary;
        if (selectedId != null) {
          for (final item in instances) {
            if (item.id == selectedId) {
              summary = item;
              break;
            }
          }
        }
        final label = summary != null
            ? '${summary.city} (${summary.stopCount})'
            : 'Instance';

        return SizedBox(
          width: 150,
          child: OutlinedButton(
            onPressed: () => _openPicker(context, ref),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
              visualDensity: VisualDensity.compact,
            ),
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12),
            ),
          ),
        );
      },
      loading: () => const SizedBox(
        width: 24,
        height: 24,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
      error: (error, stack) =>
          const Text('Instances', style: TextStyle(fontSize: 12)),
    );
  }
}

class _InstancePickerSheet extends ConsumerStatefulWidget {
  const _InstancePickerSheet({
    required this.instances,
    required this.onLoad,
  });

  final List<BenchmarkInstanceSummaryDto> instances;
  final void Function(BenchmarkInstanceDetailDto detail) onLoad;

  @override
  ConsumerState<_InstancePickerSheet> createState() =>
      _InstancePickerSheetState();
}

class _InstancePickerSheetState extends ConsumerState<_InstancePickerSheet> {
  String? _viewStopsId;
  BenchmarkInstanceDetailDto? _detail;
  bool _loadingDetail = false;

  Future<void> _viewStops(String instanceId) async {
    setState(() {
      _viewStopsId = instanceId;
      _loadingDetail = true;
      _detail = null;
    });
    try {
      final detail = await ref
          .read(apiClientProvider)
          .fetchBenchmarkInstance(instanceId);
      if (mounted) {
        setState(() {
          _detail = detail;
          _loadingDetail = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loadingDetail = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final maxHeight = MediaQuery.sizeOf(context).height * 0.75;

    return SafeArea(
      child: SizedBox(
        height: maxHeight,
        child: _viewStopsId == null
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Padding(
                    padding: EdgeInsets.fromLTRB(16, 12, 16, 8),
                    child: Text(
                      'Benchmark instances (40)',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  Expanded(
                    child: ListView.separated(
                      itemCount: widget.instances.length,
                      separatorBuilder: (context, index) =>
                          const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final item = widget.instances[index];
                        return ListTile(
                          title: Text(
                            item.id,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(
                            '${item.city} · ${item.pattern} · ${item.stopCount} stops\n${item.description}',
                          ),
                          isThreeLine: true,
                          trailing: TextButton(
                            onPressed: () => _viewStops(item.id),
                            child: const Text('View stops'),
                          ),
                          onTap: () async {
                            final detail = await ref
                                .read(apiClientProvider)
                                .fetchBenchmarkInstance(item.id);
                            widget.onLoad(detail);
                          },
                        );
                      },
                    ),
                  ),
                ],
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(8, 8, 16, 0),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_back),
                      onPressed: () {
                        setState(() {
                          _viewStopsId = null;
                          _detail = null;
                        });
                      },
                    ),
                  ),
                  if (_loadingDetail)
                    const Expanded(
                      child: Center(child: CircularProgressIndicator()),
                    )
                  else if (_detail != null)
                    Expanded(
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        children: [
                          Text(
                            _detail!.id,
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 4),
                          Text(_detail!.description),
                          const SizedBox(height: 12),
                          ..._detail!.stops.asMap().entries.map(
                                (entry) {
                                  final stop = entry.value;
                                  return Padding(
                                    padding: const EdgeInsets.only(bottom: 10),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '${entry.key + 1}. ${stop.name}',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                        Text(
                                          '${stop.lat.toStringAsFixed(5)}, ${stop.lng.toStringAsFixed(5)}',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: Colors.black54,
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                              ),
                          FilledButton(
                            onPressed: () => widget.onLoad(_detail!),
                            child: const Text('Load this instance'),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
      ),
    );
  }
}
