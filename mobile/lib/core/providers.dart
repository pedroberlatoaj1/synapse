import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/api/api_client.dart';
import 'package:synapse_mobile/core/db/database.dart';
import 'package:synapse_mobile/features/auth/auth_controller.dart';
import 'package:synapse_mobile/features/auth/auth_repository.dart';
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
  final apiClient = ApiClient(
    baseUrl: _defaultBaseUrl,
    secureStorage: secureStorage,
    forceLogout: () => ref.read(authControllerProvider.notifier).logout(),
  );

  return apiClient.dio;
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    dio: ref.watch(dioProvider),
    secureStorage: ref.watch(secureStorageProvider),
  );
});

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  final controller = AuthController(
    authRepository: ref.watch(authRepositoryProvider),
    database: ref.watch(appDatabaseProvider),
  );
  controller.restoreSession();
  return controller;
});

final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService(
    database: ref.watch(appDatabaseProvider),
    dio: ref.watch(dioProvider),
    deviceId: _defaultDeviceId,
  );
});
