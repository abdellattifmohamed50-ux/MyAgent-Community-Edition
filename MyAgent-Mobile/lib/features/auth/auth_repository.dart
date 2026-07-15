import '../../core/network/api_client.dart';
import '../../core/security/token_store.dart';
import '../../shared/models/models.dart';

class AuthRepository {
  const AuthRepository(this._api, this._tokens);

  final ApiClient _api;
  final TokenStore _tokens;

  Future<UserModel> login(String email, String password) async {
    final response = await _api.dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'email': email.trim(), 'password': password},
    );
    return _save(TokenBundle.fromJson(response.data!));
  }

  Future<UserModel> register(String name, String email, String password) async {
    final response = await _api.dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'display_name': name.trim(),
        'email': email.trim(),
        'password': password,
      },
    );
    return _save(TokenBundle.fromJson(response.data!));
  }

  Future<UserModel?> restore() async {
    if (await _tokens.readAccessToken() == null) return null;
    try {
      final response = await _api.dio.get<Map<String, dynamic>>('/auth/me');
      return UserModel.fromJson(response.data!);
    } catch (_) {
      await _tokens.clear();
      return null;
    }
  }

  Future<void> logout() async {
    final refresh = await _tokens.readRefreshToken();
    try {
      if (refresh != null) {
        await _api.dio.post<void>(
          '/auth/logout',
          data: {'refresh_token': refresh},
        );
      }
    } finally {
      await _tokens.clear();
    }
  }

  Future<UserModel> _save(TokenBundle bundle) async {
    await _tokens.save(
      accessToken: bundle.accessToken,
      refreshToken: bundle.refreshToken,
    );
    return bundle.user;
  }
}
