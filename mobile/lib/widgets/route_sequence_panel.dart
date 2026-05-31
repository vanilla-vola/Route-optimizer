import 'package:flutter/material.dart';

import '../models/models.dart';
import '../models/transport_modes.dart';

class RouteSequencePanel extends StatelessWidget {
  const RouteSequencePanel({
    super.key,
    required this.orderedStops,
    required this.totalDistanceM,
    required this.totalDurationS,
    required this.mode,
    required this.roundTrip,
  });

  final List<OrderedStopDto> orderedStops;
  final int totalDistanceM;
  final int totalDurationS;
  final String mode;
  final bool roundTrip;

  String _formatDistance(int meters) {
    if (meters >= 1000) {
      return '${(meters / 1000).toStringAsFixed(2)} km';
    }
    return '$meters m';
  }

  String _formatDuration(int seconds) {
    final minutes = seconds / 60;
    if (minutes >= 60) {
      return '${(minutes / 60).toStringAsFixed(1)} hr';
    }
    return '${minutes.toStringAsFixed(1)} min';
  }

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
              'Best route ($modeLabel${roundTrip ? ', cyclic' : ', one-way'})',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              '${_formatDistance(totalDistanceM)} · ${_formatDuration(totalDurationS)}',
              style: TextStyle(color: Colors.green.shade900),
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
