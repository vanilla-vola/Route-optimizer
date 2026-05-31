import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/solver_models.dart';
import '../providers/app_providers.dart';
import '../widgets/algorithm_picker.dart';
import '../widgets/map_panel.dart';
import '../widgets/metrics_sheets.dart';
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
  bool _benchmarkLoading = false;
  bool _compareLoading = false;
  String? _error;
  int? _totalDistanceM;
  int? _totalDurationS;
  int? _realizedDurationS;
  String? _profileSource;
  String? _solverLabel;

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
      final solverId = ref.read(selectedSolverProvider);
      final groups = ref.read(solverGroupsProvider).value ?? const [];
      final solver = findSolverOption(groups, solverId) ??
          const SolverOption(
            id: defaultSolverId,
            label: 'Route Optimizer (DCIR-Hybrid)',
            kind: SolverKind.defaultSolver,
            supportedModes: allTransportModeIds,
          );
      final result = await ref.read(apiClientProvider).runSolver(
            stops,
            roundTrip: roundTrip,
            mode: mode,
            solver: solver,
          );

      ref.read(routeOrderProvider.notifier).state = result.order;
      ref.read(orderedStopsProvider.notifier).state = result.orderedStops;
      ref.read(solverLabelProvider.notifier).state = result.solver;

      setState(() {
        _totalDistanceM = result.totalDistanceM;
        _totalDurationS = result.totalDurationS;
        _realizedDurationS = result.realizedDurationS;
        _profileSource = result.profileSource;
        _solverLabel = result.solver;
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
        _realizedDurationS = null;
        _profileSource = null;
        _solverLabel = null;
      });
      ref.read(routeOrderProvider.notifier).state = null;
      ref.read(orderedStopsProvider.notifier).state = null;
      ref.read(solverLabelProvider.notifier).state = null;
    } finally {
      setState(() => _loading = false);
    }
  }

  void _clear() {
    ref.read(stopsProvider.notifier).clear();
    ref.read(routeOrderProvider.notifier).state = null;
    ref.read(orderedStopsProvider.notifier).state = null;
    ref.read(solverLabelProvider.notifier).state = null;
    setState(() {
      _error = null;
      _totalDistanceM = null;
      _totalDurationS = null;
      _realizedDurationS = null;
      _profileSource = null;
      _solverLabel = null;
    });
  }

  Future<void> _benchmark() async {
    final stops = ref.read(stopsProvider);
    if (stops.length < 2) return;

    setState(() {
      _benchmarkLoading = true;
      _error = null;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Running all algorithms — this usually takes 1–3 minutes…',
          ),
          duration: Duration(seconds: 4),
        ),
      );
    }

    try {
      final result = await ref.read(apiClientProvider).benchmarkAlgorithms(
            stops,
            roundTrip: ref.read(roundTripProvider),
            mode: ref.read(transportModeProvider),
          );
      if (mounted) {
        await showBenchmarkSheet(context, data: result);
      }
    } catch (error) {
      setState(() => _error = formatApiError(error));
    } finally {
      if (mounted) setState(() => _benchmarkLoading = false);
    }
  }

  Future<void> _compare() async {
    final stops = ref.read(stopsProvider);
    if (stops.length < 2) return;

    setState(() {
      _compareLoading = true;
      _error = null;
    });

    try {
      final result = await ref.read(apiClientProvider).compareRoutes(
            stops,
            roundTrip: ref.read(roundTripProvider),
            mode: ref.read(transportModeProvider),
          );
      if (mounted) {
        await showCompareSheet(context, data: result);
      }
    } catch (error) {
      setState(() => _error = formatApiError(error));
    } finally {
      if (mounted) setState(() => _compareLoading = false);
    }
  }

  void _onRoundTripChanged(bool value) {
    ref.read(roundTripProvider.notifier).state = value;
    ref.read(routeOrderProvider.notifier).state = null;
    ref.read(orderedStopsProvider.notifier).state = null;
    setState(() {
      _totalDistanceM = null;
      _totalDurationS = null;
      _realizedDurationS = null;
      _profileSource = null;
      _solverLabel = null;
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

    ref.listen<String>(selectedSolverProvider, (previous, next) {
      if (previous == null || previous == next) return;
      final groups = ref.read(solverGroupsProvider).value ?? const [];
      final solver = findSolverOption(groups, next);
      if (solver != null) {
        final current = ref.read(transportModeProvider);
        final nextMode =
            pickSupportedTransportMode(current, solver.supportedModes);
        if (nextMode != current) {
          ref.read(transportModeProvider.notifier).state = nextMode;
          return;
        }
      }
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
    final selectedSolverId = ref.watch(selectedSolverProvider);
    final solverGroups = ref.watch(solverGroupsProvider).value ?? const [];
    final selectedSolver = findSolverOption(solverGroups, selectedSolverId);
    final availableModes =
        selectedSolver?.supportedModes ?? allTransportModeIds;
    final hasRoute = orderedStops != null &&
        _totalDistanceM != null &&
        _totalDurationS != null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Route Optimizer'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(52),
          child: TransportModeBar(availableModeIds: availableModes),
        ),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 12),
            child: Center(child: AlgorithmPicker()),
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
                            realizedDurationS: _realizedDurationS,
                            mode: mode,
                            solver: _solverLabel,
                            profileSource: _profileSource,
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
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: stops.length < 2 ||
                                          _compareLoading ||
                                          _loading
                                      ? null
                                      : _compare,
                                  icon: _compareLoading
                                      ? const SizedBox(
                                          width: 16,
                                          height: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.compare_arrows, size: 18),
                                  label: const Text('Compare'),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: stops.length < 2 ||
                                          _benchmarkLoading ||
                                          _loading
                                      ? null
                                      : _benchmark,
                                  icon: _benchmarkLoading
                                      ? const SizedBox(
                                          width: 16,
                                          height: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.leaderboard, size: 18),
                                  label: Text(
                                    _benchmarkLoading
                                        ? 'Benchmarking…'
                                        : 'Benchmark',
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
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
