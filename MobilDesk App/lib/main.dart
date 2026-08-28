import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'services/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/main_navigation_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const KioskoApp());
}

class KioskoApp extends StatefulWidget {
  const KioskoApp({super.key});

  @override
  State<KioskoApp> createState() => _KioskoAppState();
}

class _KioskoAppState extends State<KioskoApp> {
  final AppState _appState = AppState();

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _appState,
      builder: (context, _) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: _appState.businessName,
          theme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: const Color(0xFF2563EB),
            scaffoldBackgroundColor: const Color(0xFFF8FAFC),
            appBarTheme: const AppBarTheme(
              elevation: 0,
              centerTitle: false,
              systemOverlayStyle: SystemUiOverlayStyle.light,
            ),
            cardTheme: CardThemeData(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: const BorderSide(color: Color(0xFFE2E8F0)),
              ),
              color: Colors.white,
            ),
            inputDecorationTheme: InputDecorationTheme(
              filled: true,
              fillColor: Colors.white,
              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF2563EB), width: 2),
              ),
            ),
            filledButtonTheme: FilledButtonThemeData(
              style: FilledButton.styleFrom(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
                padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
              ),
            ),
          ),
          home: _appState.isAuthenticated
              ? MainNavigationScreen(state: _appState)
              : LoginScreen(appState: _appState),
        );
      },
    );
  }
}
