import 'dart:io';

/// Backend API base URL.
///
/// Override at run time:
///   flutter run --dart-define=API_BASE=http://192.168.1.10:8000
class ApiConfig {
  static const String _override = String.fromEnvironment('API_BASE');

  static String get baseUrl {
    if (_override.isNotEmpty) {
      return _override;
    }
    if (Platform.isAndroid) {
      // Android emulator alias for host machine localhost.
      return 'http://10.0.2.2:8000';
    }
    // iOS simulator / macOS desktop.
    return 'http://127.0.0.1:8000';
  }
}
