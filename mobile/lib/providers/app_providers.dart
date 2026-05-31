import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class StopsNotifier extends StateNotifier<List<StopDto>> {
  StopsNotifier() : super(const []);

  int addStop(StopDto stop) {
    state = [...state, stop];
    return state.length - 1;
  }

  void updateName(int index, String name) {
    final next = [...state];
    final stop = next[index];
    next[index] = StopDto(lat: stop.lat, lng: stop.lng, name: name);
    state = next;
  }

  void removeAt(int index) {
    final next = [...state]..removeAt(index);
    state = next;
  }

  void clear() => state = const [];
}

final stopsProvider = StateNotifierProvider<StopsNotifier, List<StopDto>>((ref) {
  return StopsNotifier();
});

/// Optimized visit order (indices into [stopsProvider]). Null until optimized.
final routeOrderProvider = StateProvider<List<int>?>((ref) => null);

final orderedStopsProvider =
    StateProvider<List<OrderedStopDto>?>((ref) => null);

final roundTripProvider = StateProvider<bool>((ref) => true);

final transportModeProvider = StateProvider<String>((ref) => 'driving');

final apiOnlineProvider = FutureProvider<bool>((ref) async {
  return ref.read(apiClientProvider).checkHealth();
});
