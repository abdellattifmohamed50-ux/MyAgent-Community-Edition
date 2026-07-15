import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../shared/models/models.dart';
import 'auth_repository.dart';

enum AuthStatus { initial, loading, authenticated, unauthenticated }

class AuthState {
  const AuthState({this.status = AuthStatus.initial, this.user, this.error});

  final AuthStatus status;
  final UserModel? user;
  final String? error;
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._repository) : super(const AuthState());

  final AuthRepository _repository;

  Future<void> restoreSession() async {
    state = const AuthState(status: AuthStatus.loading);
    final user = await _repository.restore();
    state = AuthState(
      status:
          user == null ? AuthStatus.unauthenticated : AuthStatus.authenticated,
      user: user,
    );
  }

  Future<bool> login(String email, String password) =>
      _authenticate(() => _repository.login(email, password));

  Future<bool> register(String name, String email, String password) =>
      _authenticate(() => _repository.register(name, email, password));

  Future<bool> _authenticate(Future<UserModel> Function() action) async {
    state = const AuthState(status: AuthStatus.loading);
    try {
      final user = await action();
      state = AuthState(status: AuthStatus.authenticated, user: user);
      return true;
    } catch (error) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        error: _message(error),
      );
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await _repository.logout();
    } finally {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  String _message(Object error) {
    final text = error.toString();
    return text.contains('401')
        ? 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
        : 'تعذر إكمال الطلب. تحقق من الاتصال وحاول مجددًا.';
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(ref.watch(authRepositoryProvider)),
);
