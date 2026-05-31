import 'models.dart';

class AlgorithmInfoDto {
  const AlgorithmInfoDto({
    required this.id,
    required this.label,
    required this.paper,
    required this.year,
    required this.category,
    this.supportedModes = const [
      'driving-traffic',
      'walking',
      'cycling',
    ],
  });

  final String id;
  final String label;
  final String paper;
  final int year;
  final String category;
  final List<String> supportedModes;

  factory AlgorithmInfoDto.fromJson(Map<String, dynamic> json) =>
      AlgorithmInfoDto(
        id: json['id'] as String,
        label: json['label'] as String,
        paper: json['paper'] as String,
        year: json['year'] as int,
        category: json['category'] as String,
        supportedModes: (json['supported_modes'] as List<dynamic>?)
                ?.map((mode) => mode as String)
                .toList() ??
            const ['driving-traffic', 'walking', 'cycling'],
      );
}

class CompareProviderInfoDto {
  const CompareProviderInfoDto({
    required this.id,
    required this.label,
    required this.kind,
    this.maxStops,
    this.requiresKey = '',
    this.supportedModes = const [
      'driving-traffic',
      'walking',
      'cycling',
    ],
  });

  final String id;
  final String label;
  final String kind;
  final int? maxStops;
  final String requiresKey;
  final List<String> supportedModes;

  factory CompareProviderInfoDto.fromJson(Map<String, dynamic> json) =>
      CompareProviderInfoDto(
        id: json['id'] as String,
        label: json['label'] as String,
        kind: json['kind'] as String,
        maxStops: json['max_stops'] as int?,
        requiresKey: json['requires_key'] as String? ?? '',
        supportedModes: (json['supported_modes'] as List<dynamic>?)
                ?.map((mode) => mode as String)
                .toList() ??
            const ['driving-traffic', 'walking', 'cycling'],
      );
}

enum SolverKind { defaultSolver, compare, research }

class SolverOption {
  const SolverOption({
    required this.id,
    required this.label,
    required this.kind,
    required this.supportedModes,
  });

  final String id;
  final String label;
  final SolverKind kind;
  final List<String> supportedModes;
}

class SolverGroup {
  const SolverGroup({
    required this.label,
    required this.options,
  });

  final String label;
  final List<SolverOption> options;
}

const defaultSolverId = 'route-optimizer';

const allTransportModeIds = ['driving-traffic', 'walking', 'cycling'];

List<String> normalizeSupportedModes(List<String>? modes) {
  if (modes == null || modes.isEmpty) {
    return allTransportModeIds;
  }
  final filtered =
      modes.where((mode) => allTransportModeIds.contains(mode)).toList();
  return filtered.isEmpty ? allTransportModeIds : filtered;
}

String pickSupportedTransportMode(String current, List<String> supportedModes) {
  if (supportedModes.contains(current)) {
    return current;
  }
  return supportedModes.first;
}

List<SolverGroup> buildSolverGroups(
  List<CompareProviderInfoDto> providers,
  List<AlgorithmInfoDto> algorithms,
) {
  CompareProviderInfoDto? ours;
  for (final provider in providers) {
    if (provider.id == defaultSolverId) {
      ours = provider;
      break;
    }
  }

  final compareApps = providers
      .where(
        (p) =>
            p.id != defaultSolverId &&
            (p.kind == 'api' || p.kind == 'manual'),
      )
      .toList()
    ..sort((a, b) {
      const order = {'api': 0, 'manual': 1};
      return (order[a.kind] ?? 2).compareTo(order[b.kind] ?? 2);
    });

  final compareInternal = providers
      .where((p) => p.id != defaultSolverId && p.kind == 'internal')
      .toList();

  final compareOptions = <SolverOption>[
    if (ours != null)
      SolverOption(
        id: ours.id,
        label: ours.label,
        kind: SolverKind.defaultSolver,
        supportedModes: normalizeSupportedModes(ours.supportedModes),
      ),
    ...compareApps.map(
      (p) => SolverOption(
        id: p.id,
        label: p.label,
        kind: SolverKind.compare,
        supportedModes: normalizeSupportedModes(p.supportedModes),
      ),
    ),
    ...compareInternal.map(
      (p) => SolverOption(
        id: p.id,
        label: p.label,
        kind: SolverKind.compare,
        supportedModes: normalizeSupportedModes(p.supportedModes),
      ),
    ),
  ];

  final researchOptions = algorithms
      .map(
        (a) => SolverOption(
          id: a.id,
          label: a.label,
          kind: SolverKind.research,
          supportedModes: normalizeSupportedModes(a.supportedModes),
        ),
      )
      .toList();

  return [
    SolverGroup(label: 'Compare', options: compareOptions),
    SolverGroup(label: 'Research algorithms', options: researchOptions),
  ];
}

SolverOption? findSolverOption(List<SolverGroup> groups, String solverId) {
  for (final group in groups) {
    for (final option in group.options) {
      if (option.id == solverId) {
        return option;
      }
    }
  }
  return null;
}

List<OrderedStopDto> buildOrderedStops(List<int> order, List<StopDto> stops) {
  return [
    for (var i = 0; i < order.length; i++)
      OrderedStopDto(
        sequence: i + 1,
        index: order[i],
        name: stops[order[i]].name,
        lat: stops[order[i]].lat,
        lng: stops[order[i]].lng,
      ),
  ];
}
