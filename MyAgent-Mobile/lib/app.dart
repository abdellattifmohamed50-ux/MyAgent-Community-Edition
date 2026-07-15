import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/auth/auth_controller.dart';
import 'features/auth/login_screen.dart';
import 'features/chat/chat_screen.dart';
import 'shared/widgets/app_splash.dart';

class MyAgentApp extends ConsumerStatefulWidget {
  const MyAgentApp({super.key});

  @override
  ConsumerState<MyAgentApp> createState() => _MyAgentAppState();
}

class _MyAgentAppState extends ConsumerState<MyAgentApp> {
  @override
  void initState() {
    super.initState();
    Future<void>.microtask(
      () => ref.read(authControllerProvider.notifier).restoreSession(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'MyAgent',
      themeMode: ThemeMode.system,
      theme: _theme(Brightness.light),
      darkTheme: _theme(Brightness.dark),
      home: switch (auth.status) {
        AuthStatus.initial || AuthStatus.loading => const AppSplash(),
        AuthStatus.authenticated => const ChatScreen(),
        AuthStatus.unauthenticated => const LoginScreen(),
      },
    );
  }

  ThemeData _theme(Brightness brightness) {
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF7557FF),
      brightness: brightness,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: brightness == Brightness.dark
          ? const Color(0xFF0D0D12)
          : const Color(0xFFF7F7FB),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    );
  }
}
