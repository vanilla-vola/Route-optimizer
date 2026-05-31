import 'package:flutter/material.dart';

/// Mapbox Directions Matrix profiles supported by the backend.
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
      id: 'driving',
      label: 'Driving',
      icon: Icons.directions_car,
    ),
    TransportModeOption(
      id: 'driving-traffic',
      label: 'Traffic',
      icon: Icons.traffic,
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
    return all.firstWhere(
      (mode) => mode.id == id,
      orElse: () => all.first,
    );
  }
}
