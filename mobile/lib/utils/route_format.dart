String formatDuration(int? seconds) {
  if (seconds == null) return '—';
  final minutes = seconds / 60;
  if (minutes >= 60) {
    return '${(minutes / 60).toStringAsFixed(1)} hr';
  }
  return '${minutes.toStringAsFixed(1)} min';
}

String formatDistance(int? meters) {
  if (meters == null) return '—';
  if (meters >= 1000) {
    return '${(meters / 1000).toStringAsFixed(2)} km';
  }
  return '$meters m';
}

String formatPct(double? pct) {
  if (pct == null) return '—';
  final sign = pct > 0 ? '+' : '';
  return '$sign${pct.toStringAsFixed(1)}%';
}

String formatProfileSource(String? source) {
  if (source == null || source.isEmpty) return '—';
  if (source == 'mapbox-depart-at') {
    return 'Mapbox traffic profiles';
  }
  if (source == 'synthetic') {
    return 'Synthetic traffic profiles';
  }
  return source;
}

String? nominalVsRealizedHint(int? nominal, int? realized) {
  if (nominal == null || realized == null || nominal <= 0) return null;
  final pct = ((realized - nominal) / nominal) * 100;
  final sign = pct > 0 ? '+' : '';
  return '$sign${pct.toStringAsFixed(1)}% vs nominal';
}
