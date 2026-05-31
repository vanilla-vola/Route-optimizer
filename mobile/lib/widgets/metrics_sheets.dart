import 'package:flutter/material.dart';

import '../models/models.dart';
import '../utils/route_format.dart';

Future<void> showBenchmarkSheet(
  BuildContext context, {
  required BenchmarkResponseDto data,
  VoidCallback? onRerun,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (context) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return BenchmarkSheetContent(
          data: data,
          scrollController: scrollController,
          onRerun: onRerun,
        );
      },
    ),
  );
}

class BenchmarkSheetContent extends StatelessWidget {
  const BenchmarkSheetContent({
    super.key,
    required this.data,
    required this.scrollController,
    this.onRerun,
  });

  final BenchmarkResponseDto data;
  final ScrollController scrollController;
  final VoidCallback? onRerun;

  @override
  Widget build(BuildContext context) {
    final okResults = data.results.where((r) => r.status == 'ok').toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Algorithm benchmark',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Profile: ${formatProfileSource(data.profileSource)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (data.rankingNote != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        data.rankingNote!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontStyle: FontStyle.italic,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
              if (onRerun != null)
                IconButton(
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Re-run benchmark',
                  onPressed: () {
                    Navigator.of(context).pop();
                    onRerun!();
                  },
                ),
            ],
          ),
        ),
        if (data.bestAlgorithmId != null ||
            data.bestRealizedAlgorithmId != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                if (data.bestAlgorithmId != null)
                  Chip(
                    label: Text('Best nominal: ${data.bestAlgorithmId}'),
                    visualDensity: VisualDensity.compact,
                  ),
                if (data.bestRealizedAlgorithmId != null)
                  Chip(
                    label: Text(
                      'Best realized: ${data.bestRealizedAlgorithmId}',
                    ),
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
          ),
        const Divider(height: 16),
        Expanded(
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 16),
            children: [
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  columnSpacing: 12,
                  headingRowHeight: 36,
                  dataRowMinHeight: 40,
                  columns: const [
                    DataColumn(label: Text('Algorithm')),
                    DataColumn(label: Text('Nominal')),
                    DataColumn(label: Text('Realized')),
                    DataColumn(label: Text('Dist')),
                    DataColumn(label: Text('vs best')),
                  ],
                  rows: okResults.map((row) {
                    final isBestNominal =
                        row.algorithmId == data.bestAlgorithmId;
                    final isBestRealized =
                        row.algorithmId == data.bestRealizedAlgorithmId;
                    return DataRow(
                      cells: [
                        DataCell(
                          Text(
                            row.algorithmLabel,
                            style: TextStyle(
                              fontWeight: isBestNominal || isBestRealized
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                            ),
                          ),
                        ),
                        DataCell(Text(formatDuration(row.totalDurationS))),
                        DataCell(
                          Text(formatDuration(row.realizedDurationS)),
                        ),
                        DataCell(Text(formatDistance(row.totalDistanceM))),
                        DataCell(
                          Text(
                            row.vsBestRealizedPct != null
                                ? formatPct(row.vsBestRealizedPct)
                                : formatPct(row.vsBestDurationPct),
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                ),
              ),
              ...data.results
                  .where((r) => r.status != 'ok')
                  .map(
                    (r) => ListTile(
                      dense: true,
                      title: Text(r.algorithmLabel),
                      subtitle: Text(r.error ?? r.status),
                    ),
                  ),
            ],
          ),
        ),
      ],
    );
  }
}

Future<void> showCompareSheet(
  BuildContext context, {
  required CompareResponseDto data,
  VoidCallback? onRerun,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (context) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.6,
      minChildSize: 0.35,
      maxChildSize: 0.9,
      builder: (context, scrollController) {
        return CompareSheetContent(
          data: data,
          scrollController: scrollController,
          onRerun: onRerun,
        );
      },
    ),
  );
}

class CompareSheetContent extends StatelessWidget {
  const CompareSheetContent({
    super.key,
    required this.data,
    required this.scrollController,
    this.onRerun,
  });

  final CompareResponseDto data;
  final ScrollController scrollController;
  final VoidCallback? onRerun;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 8, 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Compare apps',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Profile: ${formatProfileSource(data.profileSource)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    if (data.metricsNote.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        data.metricsNote,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontStyle: FontStyle.italic,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
              if (onRerun != null)
                IconButton(
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Re-run compare',
                  onPressed: () {
                    Navigator.of(context).pop();
                    onRerun!();
                  },
                ),
            ],
          ),
        ),
        const Divider(height: 16),
        Expanded(
          child: ListView.separated(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 16),
            itemCount: data.results.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final row = data.results[index];
              if (row.status == 'manual') {
                return ListTile(
                  title: Text(row.providerLabel),
                  subtitle: Text(row.message ?? 'Open manually'),
                  trailing: row.manualUrl != null
                      ? const Icon(Icons.open_in_new, size: 18)
                      : null,
                );
              }
              if (row.status != 'ok') {
                return ListTile(
                  title: Text(row.providerLabel),
                  subtitle: Text(row.message ?? row.status),
                );
              }
              return ListTile(
                title: Text(
                  row.providerLabel,
                  style: TextStyle(
                    fontWeight:
                        row.isBaseline ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                subtitle: Text(
                  [
                    formatDuration(row.totalDurationS),
                    formatDistance(row.totalDistanceM),
                    if (row.vsBaselineDurationPct != null)
                      formatPct(row.vsBaselineDurationPct),
                  ].join(' · '),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
