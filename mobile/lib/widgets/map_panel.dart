import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import '../models/models.dart';
import '../providers/app_providers.dart';

class MapPanel extends ConsumerStatefulWidget {
  const MapPanel({super.key});

  @override
  ConsumerState<MapPanel> createState() => _MapPanelState();
}

class _MapPanelState extends ConsumerState<MapPanel> {
  final MapController _mapController = MapController();

  Future<void> _resolvePlaceName(int index, double lat, double lng) async {
    try {
      final name = await ref.read(apiClientProvider).reverseGeocode(lat, lng);
      if (!mounted) return;
      final stops = ref.read(stopsProvider);
      if (index < 0 || index >= stops.length) return;
      final current = stops[index];
      if (current.lat != lat || current.lng != lng) return;
      ref.read(stopsProvider.notifier).updateName(index, name);
    } catch (_) {
      // Keep loading label or coords fallback.
    }
  }

  @override
  Widget build(BuildContext context) {
    final stops = ref.watch(stopsProvider);
    final routeOrder = ref.watch(routeOrderProvider);

    final center = stops.isEmpty
        ? const LatLng(19.076, 72.8777)
        : LatLng(
            stops.map((s) => s.lat).reduce((a, b) => a + b) / stops.length,
            stops.map((s) => s.lng).reduce((a, b) => a + b) / stops.length,
          );

    final polylinePoints = routeOrder != null
        ? _polylineForOrder(stops, routeOrder)
        : const <LatLng>[];

    return FlutterMap(
      mapController: _mapController,
      options: MapOptions(
        initialCenter: center,
        initialZoom: 12,
        onTap: (tapPosition, point) {
          final index = ref.read(stopsProvider.notifier).addStop(
                StopDto(
                  lat: point.latitude,
                  lng: point.longitude,
                  name: 'Finding place…',
                ),
              );
          ref.read(routeOrderProvider.notifier).state = null;
          ref.read(orderedStopsProvider.notifier).state = null;
          _resolvePlaceName(index, point.latitude, point.longitude);
        },
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.routeoptimizer.route_optimizer',
        ),
        if (polylinePoints.length >= 2)
          PolylineLayer(
            polylines: [
              Polyline(
                points: polylinePoints,
                color: Colors.blue.shade700,
                strokeWidth: 4,
              ),
            ],
          ),
        MarkerLayer(
          markers: [
            for (var i = 0; i < stops.length; i++)
              Marker(
                point: LatLng(stops[i].lat, stops[i].lng),
                width: 40,
                height: 40,
                child: _StopMarker(
                  stop: stops[i],
                  routePosition: routeOrder != null
                      ? routeOrder.indexOf(i) + 1
                      : null,
                ),
              ),
          ],
        ),
      ],
    );
  }

  List<LatLng> _polylineForOrder(List<StopDto> stops, List<int> order) {
    if (order.length < 2) return const [];
    return order.map((i) => LatLng(stops[i].lat, stops[i].lng)).toList();
  }
}

class _StopMarker extends StatelessWidget {
  const _StopMarker({required this.stop, this.routePosition});

  final StopDto stop;
  final int? routePosition;

  @override
  Widget build(BuildContext context) {
    final hasRoute = routePosition != null;
    return CircleAvatar(
      radius: 14,
      backgroundColor: hasRoute ? Colors.blue.shade700 : Colors.grey.shade700,
      child: Text(
        hasRoute ? '$routePosition' : '•',
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 11,
        ),
      ),
    );
  }
}
