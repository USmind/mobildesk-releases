import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'theme/design_tokens.dart';
import 'services/app_state.dart';
import 'screens/login_screen.dart';
import 'screens/user_login_screen.dart';
import 'screens/main_navigation_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark,
    ),
  );
  runApp(const KioskoApp());
}

final _appTheme = ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: DesignTokens.primary,
    brightness: Brightness.light,
    primary: DesignTokens.primary,
    onPrimary: DesignTokens.textOnPrimary,
    secondary: DesignTokens.secondary,
    onSecondary: DesignTokens.textOnPrimary,
    surface: DesignTokens.surface,
    onSurface: DesignTokens.text,
    error: DesignTokens.error,
    onError: DesignTokens.textOnPrimary,
    surfaceContainerHighest: DesignTokens.surfaceVariant,
  ),
  scaffoldBackgroundColor: DesignTokens.background,
  appBarTheme: AppBarTheme(
    elevation: 0,
    centerTitle: false,
    backgroundColor: DesignTokens.surface,
    foregroundColor: DesignTokens.text,
    surfaceTintColor: Colors.transparent,
    systemOverlayStyle: const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      statusBarBrightness: Brightness.light,
    ),
    titleTextStyle: DesignTokens.style('titleLarge').copyWith(color: DesignTokens.text),
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: DesignTokens.surface,
    indicatorColor: DesignTokens.primaryContainer,
    elevation: 0,
    labelTextStyle: WidgetStatePropertyAll(
      DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textMuted),
    ),
    iconTheme: const WidgetStatePropertyAll(
      IconThemeData(color: DesignTokens.textMuted),
    ),
  ),
  cardTheme: CardThemeData(
    elevation: 0,
    color: DesignTokens.surface,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      side: const BorderSide(color: Color(0xFFE2E8F0), width: 1),
    ),
    margin: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: DesignTokens.surface,
    contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
    border: OutlineInputBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      borderSide: const BorderSide(color: Color(0xFFE2E8F0), width: 1),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      borderSide: const BorderSide(color: Color(0xFFE2E8F0), width: 1),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      borderSide: const BorderSide(color: Color(0xFF2563EB), width: 2),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      borderSide: const BorderSide(color: Color(0xFFDC2626), width: 1),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: DesignTokens.borderRadius('md'),
      borderSide: const BorderSide(color: Color(0xFFDC2626), width: 2),
    ),
    labelStyle: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textMuted),
    hintStyle: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textMuted),
  ),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      backgroundColor: DesignTokens.primary,
      foregroundColor: DesignTokens.textOnPrimary,
      padding: DesignTokens.paddingSymmetric(h: 'lg', v: 'md'),
      shape: RoundedRectangleBorder(
        borderRadius: DesignTokens.borderRadius('md'),
      ),
      textStyle: DesignTokens.style('labelLarge'),
      // NOTA: no usar Size.fromHeight (width=infinito) porque rompe los Row:
      // el botón exige ancho infinito y comprime al Expanded a 0px
      // (texto vertical letra-por-letra en Fiados/Cobrar).
      minimumSize: const Size(64, 48),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: DesignTokens.primary,
      padding: DesignTokens.paddingSymmetric(h: 'lg', v: 'md'),
      shape: RoundedRectangleBorder(
        borderRadius: DesignTokens.borderRadius('md'),
      ),
      side: const BorderSide(color: Color(0xFF2563EB), width: 1.5),
      textStyle: DesignTokens.style('labelLarge'),
      minimumSize: const Size(64, 48),
    ),
  ),
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: DesignTokens.primary,
      padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
      shape: RoundedRectangleBorder(
        borderRadius: DesignTokens.borderRadius('md'),
      ),
      textStyle: DesignTokens.style('labelLarge'),
    ),
  ),
  dialogTheme: DialogThemeData(
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadius('lg'),
    ),
    backgroundColor: DesignTokens.surface,
    surfaceTintColor: Colors.transparent,
    titleTextStyle: DesignTokens.style('titleLarge').copyWith(color: DesignTokens.text),
    contentTextStyle: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.text),
  ),
  bottomSheetTheme: BottomSheetThemeData(
    backgroundColor: DesignTokens.surface,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadiusOnly(
        topLeft: 'xl',
        topRight: 'xl',
      ),
    ),
    modalBarrierColor: Colors.black.withAlpha(80),
  ),
  snackBarTheme: SnackBarThemeData(
    behavior: SnackBarBehavior.floating,
    backgroundColor: DesignTokens.text,
    contentTextStyle: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textOnPrimary),
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadius('md'),
    ),
    actionTextColor: DesignTokens.primaryLight,
  ),
  dividerTheme: DividerThemeData(
    color: DesignTokens.border,
    thickness: 1,
    space: 1,
  ),
  listTileTheme: ListTileThemeData(
    contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'xs'),
    titleTextStyle: DesignTokens.style('bodyLarge').copyWith(color: DesignTokens.text),
    subtitleTextStyle: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
    leadingAndTrailingTextStyle: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textMuted),
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadius('md'),
    ),
  ),
  chipTheme: ChipThemeData(
    backgroundColor: DesignTokens.surfaceVariant,
    selectedColor: DesignTokens.primaryContainer,
    labelStyle: DesignTokens.style('labelMedium'),
    secondaryLabelStyle: DesignTokens.style('labelMedium').copyWith(color: DesignTokens.textOnPrimary),
    shape: RoundedRectangleBorder(
      borderRadius: DesignTokens.borderRadius('full'),
    ),
    side: const BorderSide(color: Color(0xFFE2E8F0)),
  ),
  tooltipTheme: TooltipThemeData(
    decoration: BoxDecoration(
      color: DesignTokens.text.withAlpha(230),
      borderRadius: DesignTokens.borderRadius('sm'),
    ),
    textStyle: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textOnPrimary),
    padding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
    preferBelow: true,
  ),
);

class KioskoApp extends StatefulWidget {
  const KioskoApp({super.key});

  @override
  State<KioskoApp> createState() => _KioskoAppState();
}

class _KioskoAppState extends State<KioskoApp> {
  final AppState _appState = AppState();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: _appState.businessName,
      theme: _appTheme,
      home: ListenableBuilder(
        listenable: _appState,
        builder: (context, _) {
          if (!_appState.isAuthenticated) {
            return LoginScreen(appState: _appState);
          }
          if (_appState.appUsers.isNotEmpty && !_appState.isAppUserLoggedIn) {
            return UserLoginScreen(state: _appState);
          }
          return MainNavigationScreen(state: _appState);
        },
      ),
    );
  }
}
