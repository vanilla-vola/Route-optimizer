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
  });

  final List<int> order;
  final List<OrderedStopDto> orderedStops;
  final int totalDistanceM;
  final int totalDurationS;
  final List<LegDto> legs;
  final String mode;
  final bool roundTrip;

  factory OptimizeResponseDto.fromJson(Map<String, dynamic> json) =>
      OptimizeResponseDto(
        order: (json['order'] as List).cast<int>(),
        orderedStops: (json['ordered_stops'] as List)
            .map((e) => OrderedStopDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalDistanceM: json['total_distance_m'] as int,
        totalDurationS: json['total_duration_s'] as int,
        legs: (json['legs'] as List)
            .map((e) => LegDto.fromJson(e as Map<String, dynamic>))
            .toList(),
        mode: json['mode'] as String,
        roundTrip: json['round_trip'] as bool,
      );
}
