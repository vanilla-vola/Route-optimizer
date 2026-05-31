import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../models/models.dart';
import '../models/solver_models.dart';

class ApiClient {
  ApiClient({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: ApiConfig.baseUrl,
                connectTimeout: const Duration(seconds: 10),
                receiveTimeout: const Duration(seconds: 30),
                headers: {'Content-Type': 'application/json'},
              ),
            );

  final Dio _dio;

  /// Full benchmark runs ~15 algorithms sequentially (12s each).
  static const Duration _benchmarkTimeout = Duration(minutes: 5);

  /// Compare hits multiple external routing APIs.
  static const Duration _compareTimeout = Duration(minutes: 3);

  static const Duration _singleAlgorithmTimeout = Duration(seconds: 90);

  Future<List<PlaceSuggestionDto>> searchPlaces(
    String query, {
    int limit = 6,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/search-places',
      queryParameters: {'q': query, 'limit': limit},
    );
    final data = response.data;
    if (data == null) return const [];
    return data
        .map((e) => PlaceSuggestionDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<String> reverseGeocode(double lat, double lng) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/reverse-geocode',
      queryParameters: {'lat': lat, 'lng': lng},
    );
    final data = response.data;
    if (data == null || data['name'] is! String) {
      return '${lat.toStringAsFixed(4)}, ${lng.toStringAsFixed(4)}';
    }
    return data['name'] as String;
  }

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<OptimizeResponseDto> optimizeRoute(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/optimize-route',
      data: {
        'stops': stops.map((s) => s.toJson()).toList(),
        'round_trip': roundTrip,
        'start_fixed': false,
        'end_fixed': false,
        'mode': mode,
      },
      options: Options(receiveTimeout: _singleAlgorithmTimeout),
    );

    if (response.data == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    return OptimizeResponseDto.fromJson(response.data!);
  }

  Future<List<AlgorithmInfoDto>> listAlgorithms() async {
    final response = await _dio.get<List<dynamic>>('/algorithms');
    final data = response.data;
    if (data == null) return const [];
    return data
        .map((e) => AlgorithmInfoDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CompareProviderInfoDto>> listCompareProviders() async {
    final response = await _dio.get<List<dynamic>>('/compare-providers');
    final data = response.data;
    if (data == null) return const [];
    return data
        .map((e) => CompareProviderInfoDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<OptimizeResponseDto> compareRoute(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
    required String providerId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/compare-routes',
      data: {
        'stops': stops.map((s) => s.toJson()).toList(),
        'round_trip': roundTrip,
        'start_fixed': false,
        'end_fixed': false,
        'mode': mode,
        'provider_ids': [providerId],
      },
      options: Options(receiveTimeout: _compareTimeout),
    );

    final body = response.data;
    if (body == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    final results = body['results'] as List<dynamic>? ?? const [];
    if (results.isEmpty) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Compare provider did not return a result',
      );
    }

    final item = results.first as Map<String, dynamic>;
    final status = item['status'] as String? ?? 'error';
    if (status == 'manual') {
      throw DioException(
        requestOptions: response.requestOptions,
        message: item['message'] as String? ??
            'Open the external app to compare this route manually.',
      );
    }
    if (status != 'ok') {
      throw DioException(
        requestOptions: response.requestOptions,
        message: item['message'] as String? ??
            '${item['provider_label']} could not optimize this route',
      );
    }

    final order = (item['order'] as List<dynamic>?)?.cast<int>();
    if (order == null || order.isEmpty) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Compare provider did not return a route order',
      );
    }

    final orderedStopsJson = item['ordered_stops'] as List<dynamic>?;
    final orderedStops = orderedStopsJson != null
        ? orderedStopsJson
            .map((e) => OrderedStopDto.fromJson(e as Map<String, dynamic>))
            .toList()
        : buildOrderedStops(order, stops);

    return OptimizeResponseDto(
      order: order,
      orderedStops: orderedStops,
      totalDistanceM: item['total_distance_m'] as int? ?? 0,
      totalDurationS: item['total_duration_s'] as int? ?? 0,
      legs: const [],
      mode: mode,
      roundTrip: roundTrip,
      solver: item['provider_label'] as String?,
      profileSource: item['profile_source'] as String?,
      realizedDurationS: item['realized_duration_s'] as int?,
    );
  }

  Future<OptimizeResponseDto> benchmarkAlgorithm(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
    required String algorithmId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/benchmark-algorithms',
      data: {
        'stops': stops.map((s) => s.toJson()).toList(),
        'round_trip': roundTrip,
        'start_fixed': false,
        'end_fixed': false,
        'mode': mode,
        'algorithm_ids': [algorithmId],
        'time_limit_s': 8,
      },
      options: Options(receiveTimeout: _singleAlgorithmTimeout),
    );

    final body = response.data;
    if (body == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    final results = body['results'] as List<dynamic>? ?? const [];
    if (results.isEmpty) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Algorithm did not return a result',
      );
    }

    final item = results.first as Map<String, dynamic>;
    final status = item['status'] as String? ?? 'error';
    if (status != 'ok') {
      throw DioException(
        requestOptions: response.requestOptions,
        message: item['error'] as String? ??
            item['notes'] as String? ??
            'Algorithm failed to optimize this route',
      );
    }

    final order = (item['order'] as List<dynamic>?)?.cast<int>();
    if (order == null || order.isEmpty) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Algorithm did not return a route order',
      );
    }

    return OptimizeResponseDto(
      order: order,
      orderedStops: buildOrderedStops(order, stops),
      totalDistanceM: item['total_distance_m'] as int? ?? 0,
      totalDurationS: item['total_duration_s'] as int? ?? 0,
      legs: const [],
      mode: mode,
      roundTrip: roundTrip,
      solver: item['algorithm_label'] as String?,
      profileSource: item['profile_source'] as String?,
      realizedDurationS: item['realized_duration_s'] as int?,
    );
  }

  Future<BenchmarkResponseDto> benchmarkAlgorithms(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
    List<String>? algorithmIds,
    int timeLimitS = 12,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/benchmark-algorithms',
      data: {
        'stops': stops.map((s) => s.toJson()).toList(),
        'round_trip': roundTrip,
        'start_fixed': false,
        'end_fixed': false,
        'mode': mode,
        if (algorithmIds != null) 'algorithm_ids': algorithmIds,
        'time_limit_s': timeLimitS,
      },
      options: Options(receiveTimeout: _benchmarkTimeout),
    );

    final body = response.data;
    if (body == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    return BenchmarkResponseDto.fromJson(body);
  }

  Future<CompareResponseDto> compareRoutes(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
    List<String>? providerIds,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/compare-routes',
      data: {
        'stops': stops.map((s) => s.toJson()).toList(),
        'round_trip': roundTrip,
        'start_fixed': false,
        'end_fixed': false,
        'mode': mode,
        if (providerIds != null) 'provider_ids': providerIds,
      },
      options: Options(receiveTimeout: _compareTimeout),
    );

    final body = response.data;
    if (body == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    return CompareResponseDto.fromJson(body);
  }

  Future<OptimizeResponseDto> runSolver(
    List<StopDto> stops, {
    required bool roundTrip,
    required String mode,
    required SolverOption solver,
  }) async {
    switch (solver.kind) {
      case SolverKind.defaultSolver:
        return optimizeRoute(stops, roundTrip: roundTrip, mode: mode);
      case SolverKind.compare:
        return compareRoute(
          stops,
          roundTrip: roundTrip,
          mode: mode,
          providerId: solver.id,
        );
      case SolverKind.research:
        return benchmarkAlgorithm(
          stops,
          roundTrip: roundTrip,
          mode: mode,
          algorithmId: solver.id,
        );
    }
  }
}

String formatApiError(Object error) {
  if (error is DioException) {
    if (error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionTimeout) {
      return 'Request timed out. Benchmark runs many algorithms and can take '
          '1–3 minutes — try again, or check that the backend is running.';
    }
    final data = error.response?.data;
    if (data is Map && data['detail'] is String) {
      return data['detail'] as String;
    }
    return error.message ?? 'Network request failed';
  }
  return error.toString();
}
