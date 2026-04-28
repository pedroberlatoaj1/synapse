import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:synapse_mobile/features/auth/auth_repository.dart';

typedef AccessTokenReader = Future<String?> Function();
typedef ForceLogout = Future<void> Function();

class ApiClient {
  ApiClient({
    required String baseUrl,
    required FlutterSecureStorage secureStorage,
    AccessTokenReader? accessTokenReader,
    ForceLogout? forceLogout,
    Dio? dio,
  })  : _secureStorage = secureStorage,
        _accessTokenReader = accessTokenReader,
        _forceLogout = forceLogout,
        dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: baseUrl,
                connectTimeout: const Duration(seconds: 10),
                receiveTimeout: const Duration(seconds: 20),
                sendTimeout: const Duration(seconds: 20),
                contentType: Headers.jsonContentType,
                responseType: ResponseType.json,
              ),
            ) {
    this.dio.interceptors.add(
          QueuedInterceptorsWrapper(
            onRequest: (options, handler) async {
              if (_refreshFuture != null) {
                await _refreshFuture;
              }

              if (_isAuthEndpoint(options.path)) {
                handler.next(options);
                return;
              }

              final token = await _readAccessToken();
              if (token != null && token.isNotEmpty) {
                options.headers['Authorization'] = 'Bearer $token';
              }
              handler.next(options);
            },
            onError: (error, handler) async {
              final statusCode = error.response?.statusCode;
              final requestOptions = error.requestOptions;

              if (statusCode != 401 ||
                  _isAuthEndpoint(requestOptions.path) ||
                  requestOptions.extra['retriedAfterRefresh'] == true) {
                handler.next(error);
                return;
              }

              final refreshedAccessToken = await _refreshAccessTokenOnce();
              if (refreshedAccessToken == null) {
                await _forceLogout?.call();
                handler.next(error);
                return;
              }

              final retryHeaders = Map<String, dynamic>.from(
                requestOptions.headers,
              )..['Authorization'] = 'Bearer $refreshedAccessToken';
              final retryExtra = Map<String, dynamic>.from(requestOptions.extra)
                ..['retriedAfterRefresh'] = true;

              try {
                final retryResponse = await this.dio.fetch<Object?>(
                      requestOptions.copyWith(
                        headers: retryHeaders,
                        extra: retryExtra,
                      ),
                    );
                handler.resolve(retryResponse);
              } on DioException catch (retryError) {
                if (retryError.response?.statusCode == 401) {
                  await _forceLogout?.call();
                }
                handler.next(retryError);
              }
            },
          ),
        );
  }

  final Dio dio;
  final FlutterSecureStorage _secureStorage;
  final AccessTokenReader? _accessTokenReader;
  final ForceLogout? _forceLogout;
  Future<String?>? _refreshFuture;

  Future<String?> _readAccessToken() async {
    final tokenFromReader = await _accessTokenReader?.call();
    if (tokenFromReader != null && tokenFromReader.isNotEmpty) {
      return tokenFromReader;
    }
    return _secureStorage.read(key: accessTokenStorageKey);
  }

  Future<String?> _refreshAccessTokenOnce() {
    final activeRefresh = _refreshFuture;
    if (activeRefresh != null) {
      return activeRefresh;
    }

    final refresh = _refreshAccessToken();
    _refreshFuture = refresh;
    return refresh.whenComplete(() {
      _refreshFuture = null;
    });
  }

  Future<String?> _refreshAccessToken() async {
    final refreshToken = await _secureStorage.read(key: refreshTokenStorageKey);
    if (refreshToken == null || refreshToken.isEmpty) {
      return null;
    }

    final refreshDio = Dio(
      BaseOptions(
        baseUrl: dio.options.baseUrl,
        connectTimeout: dio.options.connectTimeout,
        receiveTimeout: dio.options.receiveTimeout,
        sendTimeout: dio.options.sendTimeout,
        contentType: Headers.jsonContentType,
        responseType: ResponseType.json,
      ),
    );

    try {
      final response = await refreshDio.post<Object?>(
        '/api/auth/refresh',
        data: {'refresh': refreshToken},
      );
      final body = _object(response.data);
      final access = body['access'];
      final refresh = body['refresh'];

      if (access is! String || access.isEmpty) {
        return null;
      }

      await _secureStorage.write(
        key: accessTokenStorageKey,
        value: access,
      );
      if (refresh is String && refresh.isNotEmpty) {
        await _secureStorage.write(
          key: refreshTokenStorageKey,
          value: refresh,
        );
      }

      return access;
    } on DioException {
      return null;
    } on FormatException {
      return null;
    }
  }

  bool _isAuthEndpoint(String path) {
    return path.startsWith('/api/auth/login') ||
        path.startsWith('/api/auth/register') ||
        path.startsWith('/api/auth/refresh');
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
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
