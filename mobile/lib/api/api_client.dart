import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../models/models.dart';

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
    );

    if (response.data == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Empty response from server',
      );
    }

    return OptimizeResponseDto.fromJson(response.data!);
  }
}

String formatApiError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data['detail'] is String) {
      return data['detail'] as String;
    }
    return error.message ?? 'Network request failed';
  }
  return error.toString();
}
