import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:synapse_mobile/core/providers.dart';
import 'package:synapse_mobile/features/auth/auth_controller.dart';
import 'package:synapse_mobile/features/auth/login_screen.dart';
import 'package:synapse_mobile/features/decks/decks_screen.dart';

void main() {
  runApp(const ProviderScope(child: SynapseApp()));
}

class SynapseApp extends StatelessWidget {
  const SynapseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Synapse',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);

    switch (authState.status) {
      case AuthStatus.loading:
        return const Scaffold(
          backgroundColor: Color(0xFF09090B),
          body: Center(child: CircularProgressIndicator()),
        );
      case AuthStatus.authenticated:
        return const DecksScreen();
      case AuthStatus.unauthenticated:
        return const LoginScreen();
    }
  }
}
