class PlaceSuggestionDto {
  const PlaceSuggestionDto({
    required this.name,
    required this.lat,
    required this.lng,
    this.subtitle = '',
  });

  final String name;
  final double lat;
  final double lng;
  final String subtitle;

  factory PlaceSuggestionDto.fromJson(Map<String, dynamic> json) =>
      PlaceSuggestionDto(
        name: json['name'] as String,
        lat: (json['lat'] as num).toDouble(),
        lng: (json['lng'] as num).toDouble(),
        subtitle: json['subtitle'] as String? ?? '',
      );
}

class StopDto {
  const StopDto({
    required this.lat,
    required this.lng,
    required this.name,
  });

  final double lat;
  final double lng;
  final String name;

  Map<String, dynamic> toJson() => {
        'lat': lat,
        'lng': lng,
        'name': name,
      };

  factory StopDto.fromJson(Map<String, dynamic> json) => StopDto(
        lat: (json['lat'] as num).toDouble(),
        lng: (json['lng'] as num).toDouble(),
        name: json['name'] as String? ?? '',
      );
}

class OrderedStopDto {
  const OrderedStopDto({
    required this.sequence,
    required this.index,
    required this.name,
    required this.lat,
    required this.lng,
  });

  final int sequence;
  final int index;
  final String name;
  final double lat;
  final double lng;

  factory OrderedStopDto.fromJson(Map<String, dynamic> json) => OrderedStopDto(
        sequence: json['sequence'] as int,
        index: json['index'] as int,
        name: json['name'] as String,
        lat: (json['lat'] as num).toDouble(),
        lng: (json['lng'] as num).toDouble(),
      );
}

class LegDto {
  const LegDto({
    required this.fromIndex,
    required this.toIndex,
    required this.distanceM,
    required this.durationS,
  });

  final int fromIndex;
  final int toIndex;
  final int distanceM;
  final int durationS;

  factory LegDto.fromJson(Map<String, dynamic> json) => LegDto(
        fromIndex: json['from_index'] as int,
        toIndex: json['to_index'] as int,
        distanceM: json['distance_m'] as int,
        durationS: json['duration_s'] as int,
      );
}

class OptimizeResponseDto {
  const OptimizeResponseDto({
    required this.order,
    required this.orderedStops,
    required this.totalDistanceM,
    required this.totalDurationS,
    required this.legs,
    required this.mode,
    required this.roundTrip,
    this.solver,
    this.profileSource,
    this.realizedDurationS,
  });

  final List<int> order;
  final List<OrderedStopDto> orderedStops;
  final int totalDistanceM;
  final int totalDurationS;
  final List<LegDto> legs;
  final String mode;
  final bool roundTrip;
  final String? solver;
  final String? profileSource;
  final int? realizedDurationS;

  factory OptimizeResponseDto.fromJson(Map<String, dynamic> json) =>
      OptimizeResponseDto(
        order: (json['order'] as List).cast<int>(),
        orderedStops: (json['ordered_stops'] as List)
            .map((e) => OrderedStopDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalDistanceM: json['total_distance_m'] as int,
        totalDurationS: json['total_duration_s'] as int,
        legs: (json['legs'] as List? ?? const [])
            .map((e) => LegDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        mode: json['mode'] as String,
        roundTrip: json['round_trip'] as bool,
        solver: json['solver'] as String?,
        profileSource: json['profile_source'] as String?,
        realizedDurationS: json['realized_duration_s'] as int?,
      );
}

class BenchmarkResultDto {
  const BenchmarkResultDto({
    required this.algorithmId,
    required this.algorithmLabel,
    required this.status,
    this.totalDurationS,
    this.realizedDurationS,
    this.totalDistanceM,
    this.vsBestDurationPct,
    this.vsBestRealizedPct,
    this.category,
    this.error,
  });

  final String algorithmId;
  final String algorithmLabel;
  final String status;
  final int? totalDurationS;
  final int? realizedDurationS;
  final int? totalDistanceM;
  final double? vsBestDurationPct;
  final double? vsBestRealizedPct;
  final String? category;
  final String? error;

  factory BenchmarkResultDto.fromJson(Map<String, dynamic> json) =>
      BenchmarkResultDto(
        algorithmId: json['algorithm_id'] as String,
        algorithmLabel: json['algorithm_label'] as String,
        status: json['status'] as String,
        totalDurationS: json['total_duration_s'] as int?,
        realizedDurationS: json['realized_duration_s'] as int?,
        totalDistanceM: json['total_distance_m'] as int?,
        vsBestDurationPct: (json['vs_best_duration_pct'] as num?)?.toDouble(),
        vsBestRealizedPct: (json['vs_best_realized_pct'] as num?)?.toDouble(),
        category: json['category'] as String?,
        error: json['error'] as String?,
      );
}

class BenchmarkResponseDto {
  const BenchmarkResponseDto({
    required this.results,
    required this.profileSource,
    this.bestAlgorithmId,
    this.bestRealizedAlgorithmId,
    this.rankingNote,
  });

  final List<BenchmarkResultDto> results;
  final String profileSource;
  final String? bestAlgorithmId;
  final String? bestRealizedAlgorithmId;
  final String? rankingNote;

  factory BenchmarkResponseDto.fromJson(Map<String, dynamic> json) =>
      BenchmarkResponseDto(
        results: (json['results'] as List? ?? const [])
            .map((e) => BenchmarkResultDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        profileSource: json['profile_source'] as String? ?? 'synthetic',
        bestAlgorithmId: json['best_algorithm_id'] as String?,
        bestRealizedAlgorithmId: json['best_realized_algorithm_id'] as String?,
        rankingNote: json['ranking_note'] as String?,
      );
}

class CompareResultDto {
  const CompareResultDto({
    required this.providerId,
    required this.providerLabel,
    required this.status,
    this.totalDurationS,
    this.totalDistanceM,
    this.vsBaselineDurationPct,
    this.isBaseline = false,
    this.message,
    this.manualUrl,
  });

  final String providerId;
  final String providerLabel;
  final String status;
  final int? totalDurationS;
  final int? totalDistanceM;
  final double? vsBaselineDurationPct;
  final bool isBaseline;
  final String? message;
  final String? manualUrl;

  factory CompareResultDto.fromJson(Map<String, dynamic> json) =>
      CompareResultDto(
        providerId: json['provider_id'] as String,
        providerLabel: json['provider_label'] as String,
        status: json['status'] as String,
        totalDurationS: json['total_duration_s'] as int?,
        totalDistanceM: json['total_distance_m'] as int?,
        vsBaselineDurationPct:
            (json['vs_baseline_duration_pct'] as num?)?.toDouble(),
        isBaseline: json['is_baseline'] as bool? ?? false,
        message: json['message'] as String?,
        manualUrl: json['manual_url'] as String?,
      );
}

class BenchmarkInstanceSummaryDto {
  const BenchmarkInstanceSummaryDto({
    required this.id,
    required this.description,
    required this.city,
    required this.region,
    required this.pattern,
    required this.stopCount,
    required this.mode,
    required this.roundTrip,
  });

  final String id;
  final String description;
  final String city;
  final String region;
  final String pattern;
  final int stopCount;
  final String mode;
  final bool roundTrip;

  factory BenchmarkInstanceSummaryDto.fromJson(Map<String, dynamic> json) =>
      BenchmarkInstanceSummaryDto(
        id: json['id'] as String,
        description: json['description'] as String,
        city: json['city'] as String,
        region: json['region'] as String,
        pattern: json['pattern'] as String,
        stopCount: json['stop_count'] as int,
        mode: json['mode'] as String,
        roundTrip: json['round_trip'] as bool,
      );
}

class BenchmarkInstanceDetailDto {
  const BenchmarkInstanceDetailDto({
    required this.id,
    required this.description,
    required this.city,
    required this.region,
    required this.pattern,
    required this.mode,
    required this.roundTrip,
    required this.stops,
  });

  final String id;
  final String description;
  final String city;
  final String region;
  final String pattern;
  final String mode;
  final bool roundTrip;
  final List<StopDto> stops;

  factory BenchmarkInstanceDetailDto.fromJson(Map<String, dynamic> json) =>
      BenchmarkInstanceDetailDto(
        id: json['id'] as String,
        description: json['description'] as String,
        city: json['city'] as String,
        region: json['region'] as String,
        pattern: json['pattern'] as String,
        mode: json['mode'] as String,
        roundTrip: json['round_trip'] as bool,
        stops: (json['stops'] as List)
            .map((e) => StopDto.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class BenchmarkInstanceListResponseDto {
  const BenchmarkInstanceListResponseDto({
    required this.count,
    required this.instances,
  });

  final int count;
  final List<BenchmarkInstanceSummaryDto> instances;

  factory BenchmarkInstanceListResponseDto.fromJson(
    Map<String, dynamic> json,
  ) =>
      BenchmarkInstanceListResponseDto(
        count: json['count'] as int,
        instances: (json['instances'] as List)
            .map(
              (e) => BenchmarkInstanceSummaryDto.fromJson(
                e as Map<String, dynamic>,
              ),
            )
            .toList(),
      );
}

class CompareResponseDto {
  const CompareResponseDto({
    required this.results,
    required this.profileSource,
    this.metricsNote = '',
  });

  final List<CompareResultDto> results;
  final String profileSource;
  final String metricsNote;

  factory CompareResponseDto.fromJson(Map<String, dynamic> json) =>
      CompareResponseDto(
        results: (json['results'] as List? ?? const [])
            .map((e) => CompareResultDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        profileSource: json['profile_source'] as String? ?? 'synthetic',
        metricsNote: json['metrics_note'] as String? ?? '',
      );
}
