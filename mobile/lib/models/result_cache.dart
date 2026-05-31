import 'models.dart';

/// Fingerprint for whether cached benchmark/compare results still apply.
String routeContextFingerprint(
  List<StopDto> stops, {
  required String mode,
  required bool roundTrip,
}) {
  final stopPart =
      stops.map((s) => '${s.lat.toStringAsFixed(5)},${s.lng.toStringAsFixed(5)}').join('|');
  return '$stopPart::$mode::$roundTrip';
}

class BenchmarkCacheEntry {
  const BenchmarkCacheEntry({
    required this.data,
    required this.fingerprint,
  });

  final BenchmarkResponseDto data;
  final String fingerprint;

  bool matches(String fingerprint) => this.fingerprint == fingerprint;
}

class CompareCacheEntry {
  const CompareCacheEntry({
    required this.data,
    required this.fingerprint,
  });

  final CompareResponseDto data;
  final String fingerprint;

  bool matches(String fingerprint) => this.fingerprint == fingerprint;
}
