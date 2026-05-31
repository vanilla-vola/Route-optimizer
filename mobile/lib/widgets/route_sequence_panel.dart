import 'package:flutter/material.dart';

import '../models/models.dart';
import '../models/transport_modes.dart';
import 'route_metrics_panel.dart';

class RouteSequencePanel extends StatelessWidget {
  const RouteSequencePanel({
    super.key,
    required this.orderedStops,
    required this.totalDistanceM,
    required this.totalDurationS,
    required this.mode,
    this.realizedDurationS,
    this.solver,
    this.profileSource,
  });

  final List<OrderedStopDto> orderedStops;
  final int totalDistanceM;
  final int totalDurationS;
  final int? realizedDurationS;
  final String mode;
  final String? solver;
  final String? profileSource;

  @override
  Widget build(BuildContext context) {
    final modeLabel = TransportModeOption.byId(mode).label;

    return Card(
      margin: const EdgeInsets.fromLTRB(12, 4, 12, 4),
      color: Colors.green.shade50,
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Best route ($modeLabel)',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            RouteMetricsPanel(
              nominalDurationS: totalDurationS,
              realizedDurationS: realizedDurationS,
              totalDistanceM: totalDistanceM,
              solver: solver,
              profileSource: profileSource,
            ),
            const SizedBox(height: 12),
            Text(
              'Visit in this order:',
              style: Theme.of(context).textTheme.labelLarge,
            ),
            const SizedBox(height: 8),
            ...orderedStops.map(
              (stop) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 12,
                      backgroundColor: Colors.green.shade700,
                      child: Text(
                        '${stop.sequence}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            stop.name,
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          Text(
                            '${stop.lat.toStringAsFixed(5)}, ${stop.lng.toStringAsFixed(5)}',
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.black54,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
