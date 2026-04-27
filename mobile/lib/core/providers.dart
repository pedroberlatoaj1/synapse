import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/features/sync/sync_service.dart';

const _defaultBaseUrl = String.fromEnvironment(
  'SYNAPSE_API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

const _defaultDeviceId = String.fromEnvironment(
  'SYNAPSE_DEVICE_ID',
  defaultValue: 'synapse-flutter-dev',
);

final appDatabaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(database.close);
  return database;
});

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final dioProvider = Provider<Dio>((ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  final dio = Dio(
    BaseOptions(
      baseUrl: _defaultBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      sendTimeout: const Duration(seconds: 20),
      contentType: Headers.jsonContentType,
      responseType: ResponseType.json,
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        options.headers.putIfAbsent('Accept', () => Headers.jsonContentType);
        final token = await secureStorage.read(key: 'jwt_token');
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ),
  );

  return dio;
});

final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService(
    database: ref.watch(appDatabaseProvider),
    dio: ref.watch(dioProvider),
    deviceId: _defaultDeviceId,
  );
});
