import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../security/token_store.dart';

class ApiClient {
  ApiClient(this._tokens)
      : dio = Dio(
          BaseOptions(
            baseUrl: AppConfig.apiBaseUrl,
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 90),
            headers: const {'Content-Type': 'application/json'},
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokens.readAccessToken();
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode != 401 ||
              error.requestOptions.extra['retried'] == true ||
              _refreshExcluded(error.requestOptions.path)) {
            handler.next(error);
            return;
          }
          try {
            final accessToken = await _refreshAccessToken();
            if (accessToken == null) {
              handler.next(error);
              return;
            }
            final options = error.requestOptions;
            options.extra['retried'] = true;
            options.headers['Authorization'] = 'Bearer $accessToken';
            handler.resolve(await dio.fetch(options));
          } catch (_) {
            await _tokens.clear();
            handler.next(error);
          }
        },
      ),
    );
  }

  final TokenStore _tokens;
  final Dio dio;
  Future<String?>? _refreshing;

  Future<String?> _refreshAccessToken() {
    final active = _refreshing;
    if (active != null) return active;
    final request = _performRefresh();
    _refreshing = request;
    return request.whenComplete(() => _refreshing = null);
  }

  Future<String?> _performRefresh() async {
    final refreshToken = await _tokens.readRefreshToken();
    if (refreshToken == null) return null;
    final refreshClient = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        headers: const {'Content-Type': 'application/json'},
      ),
    );
    try {
      final response = await refreshClient.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final data = response.data!;
      final accessToken = data['access_token'] as String;
      await _tokens.save(
        accessToken: accessToken,
        refreshToken: data['refresh_token'] as String,
      );
      return accessToken;
    } finally {
      refreshClient.close(force: true);
    }
  }

  void close() => dio.close(force: true);
}

bool _refreshExcluded(String path) => const {
      '/auth/login',
      '/auth/register',
      '/auth/refresh',
      '/auth/logout',
    }.any(path.endsWith);
