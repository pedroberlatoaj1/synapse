import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const accessTokenStorageKey = 'synapse_access_token';
const refreshTokenStorageKey = 'synapse_refresh_token';

class AuthTokens {
  const AuthTokens({
    required this.access,
    required this.refresh,
  });

  factory AuthTokens.fromJson(Map<String, Object?> json) {
    final access = json['access'];
    final refresh = json['refresh'];

    if (access is! String || access.isEmpty) {
      throw const FormatException('Expected non-empty access token.');
    }
    if (refresh is! String || refresh.isEmpty) {
      throw const FormatException('Expected non-empty refresh token.');
    }

    return AuthTokens(access: access, refresh: refresh);
  }

  final String access;
  final String refresh;
}

class AuthRepository {
  const AuthRepository({
    required Dio dio,
    required FlutterSecureStorage secureStorage,
  })  : _dio = dio,
        _secureStorage = secureStorage;

  final Dio _dio;
  final FlutterSecureStorage _secureStorage;

  Future<AuthTokens> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post<Object?>(
      '/api/auth/login',
      data: {
        'email': email.trim(),
        'password': password,
      },
    );
    final tokens = AuthTokens.fromJson(_object(response.data));

    await _secureStorage.write(
      key: accessTokenStorageKey,
      value: tokens.access,
    );
    await _secureStorage.write(
      key: refreshTokenStorageKey,
      value: tokens.refresh,
    );

    return tokens;
  }

  Future<void> logout() async {
    await _secureStorage.delete(key: accessTokenStorageKey);
    await _secureStorage.delete(key: refreshTokenStorageKey);
  }

  Future<bool> hasValidSession() async {
    final accessToken = await readAccessToken();
    return accessToken != null && accessToken.isNotEmpty;
  }

  Future<String?> readAccessToken() {
    return _secureStorage.read(key: accessTokenStorageKey);
  }

  Future<String?> readRefreshToken() {
    return _secureStorage.read(key: refreshTokenStorageKey);
  }
}

Map<String, Object?> _object(Object? value) {
  if (value is Map<String, Object?>) {
    return value;
  }
  if (value is Map) {
    return value.cast<String, Object?>();
  }
  throw const FormatException('Expected JSON object.');
}
