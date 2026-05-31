import 'package:flutter/material.dart';

import '../utils/route_format.dart';

class RouteMetricsPanel extends StatelessWidget {
  const RouteMetricsPanel({
    super.key,
    required this.nominalDurationS,
    this.realizedDurationS,
    required this.totalDistanceM,
    this.solver,
    this.profileSource,
  });

  final int nominalDurationS;
  final int? realizedDurationS;
  final int totalDistanceM;
  final String? solver;
  final String? profileSource;

  @override
  Widget build(BuildContext context) {
    final hint = nominalVsRealizedHint(nominalDurationS, realizedDurationS);

    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _MetricCard(
                label: 'Nominal duration',
                value: formatDuration(nominalDurationS),
                hint: 'Static matrix snapshot',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _MetricCard(
                label: 'Realized duration',
                value: formatDuration(realizedDurationS),
                hint: hint ?? 'Departure-consistent traffic',
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _MetricCard(
                label: 'Distance',
                value: formatDistance(totalDistanceM),
              ),
            ),
            if (solver != null) ...[
              const SizedBox(width: 8),
              Expanded(
                child: _MetricCard(
                  label: 'Solver',
                  value: solver!,
                  hint: formatProfileSource(profileSource),
                  smallValue: true,
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    this.hint,
    this.smallValue = false,
  });

  final String label;
  final String value;
  final String? hint;
  final bool smallValue;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              letterSpacing: 0.4,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: smallValue ? 12 : 16,
              fontWeight: FontWeight.bold,
              color: Colors.green.shade900,
            ),
          ),
          if (hint != null && hint!.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              hint!,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
            ),
          ],
        ],
      ),
    );
  }
}
