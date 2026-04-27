import 'package:dio/dio.dart';
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

final dioProvider = Provider<Dio>((ref) {
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
      onRequest: (options, handler) {
        options.headers.putIfAbsent('Accept', () => Headers.jsonContentType);
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
