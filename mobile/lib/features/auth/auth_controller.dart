import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/features/auth/auth_repository.dart';

enum AuthStatus {
  loading,
  authenticated,
  unauthenticated,
}

class AuthState {
  const AuthState({
    required this.status,
    this.errorMessage,
  });

  const AuthState.loading() : this(status: AuthStatus.loading);

  const AuthState.authenticated() : this(status: AuthStatus.authenticated);

  const AuthState.unauthenticated({String? errorMessage})
      : this(
          status: AuthStatus.unauthenticated,
          errorMessage: errorMessage,
        );

  final AuthStatus status;
  final String? errorMessage;

  bool get isLoading => status == AuthStatus.loading;
  bool get isAuthenticated => status == AuthStatus.authenticated;
}

class AuthController extends StateNotifier<AuthState> {
  AuthController({
    required AuthRepository authRepository,
    required AppDatabase database,
  })  : _authRepository = authRepository,
        _database = database,
        super(const AuthState.loading());

  final AuthRepository _authRepository;
  final AppDatabase _database;

  Future<void> restoreSession() async {
    try {
      final hasSession = await _authRepository.hasValidSession();
      state = hasSession
          ? const AuthState.authenticated()
          : const AuthState.unauthenticated();
    } catch (error) {
      state = AuthState.unauthenticated(errorMessage: error.toString());
    }
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AuthState.loading();

    try {
      await _authRepository.login(email: email, password: password);
      state = const AuthState.authenticated();
    } catch (error) {
      state = AuthState.unauthenticated(
        errorMessage: 'Falha ao entrar: $error',
      );
    }
  }

  Future<void> logout() async {
    state = const AuthState.loading();

    try {
      await _authRepository.logout();
      await _clearLocalDatabase();
    } finally {
      state = const AuthState.unauthenticated();
    }
  }

  Future<void> _clearLocalDatabase() {
    return _database.transaction(() async {
      await _database.delete(_database.syncEvents).go();
      await _database.delete(_database.localCards).go();
      await _database.delete(_database.localDecks).go();
    });
  }
}
