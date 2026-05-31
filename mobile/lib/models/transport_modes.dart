import 'package:flutter/material.dart';

/// Mapbox profiles exposed in the app (car uses driving-traffic for realistic ETAs).
class TransportModeOption {
  const TransportModeOption({
    required this.id,
    required this.label,
    required this.icon,
  });

  final String id;
  final String label;
  final IconData icon;

  static const List<TransportModeOption> all = [
    TransportModeOption(
      id: 'driving-traffic',
      label: 'Driving',
      icon: Icons.directions_car,
    ),
    TransportModeOption(
      id: 'walking',
      label: 'Walking',
      icon: Icons.directions_walk,
    ),
    TransportModeOption(
      id: 'cycling',
      label: 'Cycling',
      icon: Icons.directions_bike,
    ),
  ];

  static TransportModeOption byId(String id) {
    if (id == 'driving') {
      return all.first;
    }
    return all.firstWhere(
      (mode) => mode.id == id,
      orElse: () => all.first,
    );
  }
}
