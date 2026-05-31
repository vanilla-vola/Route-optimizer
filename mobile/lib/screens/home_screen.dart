import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../providers/app_providers.dart';
import '../widgets/map_panel.dart';
import '../widgets/route_sequence_panel.dart';
import '../widgets/stop_list.dart';
import '../widgets/stop_search_bar.dart';
import '../widgets/transport_mode_bar.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _loading = false;
  String? _error;
  int? _totalDistanceM;
  int? _totalDurationS;

  Future<void> _optimize() async {
    final stops = ref.read(stopsProvider);
    if (stops.length < 2) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final roundTrip = ref.read(roundTripProvider);
      final mode = ref.read(transportModeProvider);
      final result = await ref.read(apiClientProvider).optimizeRoute(
            stops,
            roundTrip: roundTrip,
            mode: mode,
          );

      ref.read(routeOrderProvider.notifier).state = result.order;
      ref.read(orderedStopsProvider.notifier).state = result.orderedStops;

      setState(() {
        _totalDistanceM = result.totalDistanceM;
        _totalDurationS = result.totalDurationS;
      });

      if (mounted) {
        final names = result.orderedStops.map((s) => s.name).join(' → ');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Route: $names')),
        );
      }
    } catch (error) {
      setState(() {
        _error = formatApiError(error);
        _totalDistanceM = null;
        _totalDurationS = null;
      });
      ref.read(routeOrderProvider.notifier).state = null;
      ref.read(orderedStopsProvider.notifier).state = null;
    } finally {
      setState(() => _loading = false);
    }
  }

  void _clear() {
    ref.read(stopsProvider.notifier).clear();
    ref.read(routeOrderProvider.notifier).state = null;
    ref.read(orderedStopsProvider.notifier).state = null;
    setState(() {
      _error = null;
      _totalDistanceM = null;
      _totalDurationS = null;
    });
  }

  void _onRoundTripChanged(bool value) {
    ref.read(roundTripProvider.notifier).state = value;
    ref.read(routeOrderProvider.notifier).state = null;
    ref.read(orderedStopsProvider.notifier).state = null;
    setState(() {
      _totalDistanceM = null;
      _totalDurationS = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<String>(transportModeProvider, (previous, next) {
      if (previous == null || previous == next) return;
      final ordered = ref.read(orderedStopsProvider);
      final stops = ref.read(stopsProvider);
      if (ordered != null && stops.length >= 2) {
        _optimize();
      }
    });

    final stops = ref.watch(stopsProvider);
    final roundTrip = ref.watch(roundTripProvider);
    final orderedStops = ref.watch(orderedStopsProvider);
    final mode = ref.watch(transportModeProvider);
    final apiOnline = ref.watch(apiOnlineProvider);
    final hasRoute = orderedStops != null &&
        _totalDistanceM != null &&
        _totalDurationS != null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Route Optimizer'),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(52),
          child: TransportModeBar(),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: apiOnline.when(
                data: (online) => Chip(
                  label: Text(
                    online ? 'API online' : 'API offline',
                    style: const TextStyle(fontSize: 12),
                  ),
                  backgroundColor:
                      online ? Colors.green.shade100 : Colors.red.shade100,
                ),
                loading: () => const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                error: (error, stackTrace) =>
                    const Chip(label: Text('API offline')),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          const Expanded(flex: 3, child: MapPanel()),
          const Divider(height: 1),
          Expanded(
            flex: 2,
            child: Column(
              children: [
                Expanded(
                  child: CustomScrollView(
                    slivers: [
                      const SliverPadding(
                        padding: EdgeInsets.fromLTRB(16, 10, 16, 8),
                        sliver: SliverToBoxAdapter(child: StopSearchBar()),
                      ),
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 4),
                        sliver: SliverToBoxAdapter(
                          child: Text(
                            'Selected spots (${stops.length})',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                      ),
                      const StopListSliver(),
                      SliverToBoxAdapter(
                        child: SwitchListTile(
                          dense: true,
                          contentPadding:
                              const EdgeInsets.symmetric(horizontal: 8),
                          title: const Text(
                            'Return to start (cyclic)',
                            style: TextStyle(fontSize: 14),
                          ),
                          subtitle: const Text(
                            'First stop is start and end',
                            style: TextStyle(fontSize: 12),
                          ),
                          value: roundTrip,
                          onChanged: _onRoundTripChanged,
                        ),
                      ),
                      if (hasRoute)
                        SliverToBoxAdapter(
                          child: RouteSequencePanel(
                            orderedStops: orderedStops,
                            totalDistanceM: _totalDistanceM!,
                            totalDurationS: _totalDurationS!,
                            mode: mode,
                          ),
                        ),
                      if (_error != null)
                        SliverPadding(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                          sliver: SliverToBoxAdapter(
                            child: Text(
                              _error!,
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.error,
                              ),
                            ),
                          ),
                        ),
                      const SliverPadding(padding: EdgeInsets.only(bottom: 8)),
                    ],
                  ),
                ),
                Material(
                  elevation: 6,
                  color: Theme.of(context).colorScheme.surface,
                  child: SafeArea(
                    top: false,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed:
                                  stops.length < 2 || _loading ? null : _optimize,
                              icon: _loading
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Icon(Icons.route),
                              label: Text(
                                _loading ? 'Optimizing…' : 'Optimize route',
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          IconButton.filledTonal(
                            onPressed: stops.isEmpty ? null : _clear,
                            icon: const Icon(Icons.clear),
                            tooltip: 'Clear stops',
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
