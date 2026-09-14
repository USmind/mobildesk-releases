/// Tokens de diseño centralizados para MobilDesk App
/// Inspirado en design-tokens.json del proyecto desktop
/// Único punto de verdad para colores, espaciado, radios, tipografía

import 'package:flutter/material.dart';

class DesignTokens {
  DesignTokens._();

  // ──────────────────────────────────────────────
  // COLORES
  // ──────────────────────────────────────────────
  static const Color primary = Color(0xFF2563EB);       // Blue 600
  static const Color primaryLight = Color(0xFF3B82F6);  // Blue 500
  static const Color primaryDark = Color(0xFF1D4ED8);   // Blue 700
  static const Color primaryContainer = Color(0xFFDBEAFE); // Blue 50

  static const Color secondary = Color(0xFF0B0F1A);     // Escritorio: banner oscuro
  static const Color secondaryDark = Color(0xFF0B0F1A);
  static const Color secondaryContainer = Color(0xFFF7F8FA);

  static const Color background = Color(0xFFF7F8FA);    // Fondo MobilDesk POS
  static const Color surface = Color(0xFFFFFFFF);       // White
  static const Color surfaceVariant = Color(0xFFEDF0F4); // Superficie suave

  static const Color text = Color(0xFF131722);          // Tinta MobilDesk POS
  static const Color textSecondary = Color(0xFF343B48);
  static const Color textMuted = Color(0xFF6B7280);
  static const Color textOnPrimary = Color(0xFFFFFFFF); // White

  static const Color border = Color(0xFFE4E7EC);
  static const Color borderStrong = Color(0xFFC9CED6);

  static const Color error = Color(0xFFDC2626);         // Red 600
  static const Color errorContainer = Color(0xFFFEF2F2); // Red 50
  static const Color errorLight = Color(0xFFEF4444);    // Red 500

  static const Color success = Color(0xFF16A34A);       // Green 600
  static const Color successContainer = Color(0xFFF0FDF4); // Green 50
  static const Color successLight = Color(0xFF22C55E);  // Green 500

  static const Color warning = Color(0xFFD97706);       // Amber 600
  static const Color warningContainer = Color(0xFFFFFBEB); // Amber 50
  static const Color warningLight = Color(0xFFF59E0B);  // Amber 500

  static const Color info = Color(0xFF2563EB);          // Blue 600
  static const Color infoContainer = Color(0xFFDBEAFE);  // Blue 50

  // ──────────────────────────────────────────────
  // ESPACIADO (spacing scale)
  // ──────────────────────────────────────────────
  static const Map<String, double> spacing = {
    'none': 0,
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
    '2xl': 48,
    '3xl': 64,
  };

  // Helpers para espaciado común
  static const double spaceXs = 4;
  static const double spaceSm = 8;
  static const double spaceMd = 16;
  static const double spaceLg = 24;
  static const double spaceXl = 32;

  // ──────────────────────────────────────────────
  // RADIOS (border radius)
  // ──────────────────────────────────────────────
  static const Map<String, double> radius = {
    'none': 0,
    'xs': 4,
    'sm': 6,
    'md': 10,
    'lg': 12,
    'xl': 16,
    '2xl': 20,
    'full': 9999,
  };

  // Helpers para radios comunes
  static const double radiusSm = 6;
  static const double radiusMd = 10;
  static const double radiusLg = 12;
  static const double radiusXl = 16;
  static const double radiusFull = 9999;

  // ──────────────────────────────────────────────
  // TIPGRAFÍA
  // ──────────────────────────────────────────────
  static const Map<String, TextStyle> textStyles = {
    'displayLarge': TextStyle(
      fontSize: 57,
      fontWeight: FontWeight.w400,
      letterSpacing: -0.25,
      height: 1.12,
    ),
    'displayMedium': TextStyle(
      fontSize: 45,
      fontWeight: FontWeight.w400,
      letterSpacing: 0,
      height: 1.16,
    ),
    'displaySmall': TextStyle(
      fontSize: 36,
      fontWeight: FontWeight.w400,
      letterSpacing: 0,
      height: 1.22,
    ),
    'headlineLarge': TextStyle(
      fontSize: 32,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
      height: 1.25,
    ),
    'headlineMedium': TextStyle(
      fontSize: 28,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
      height: 1.29,
    ),
    'headlineSmall': TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
      height: 1.33,
    ),
    'titleLarge': TextStyle(
      fontSize: 22,
      fontWeight: FontWeight.w600,
      letterSpacing: 0,
      height: 1.27,
    ),
    'titleMedium': TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.15,
      height: 1.5,
    ),
    'titleSmall': TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.1,
      height: 1.43,
    ),
    'bodyLarge': TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w400,
      letterSpacing: 0.5,
      height: 1.5,
    ),
    'bodyMedium': TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.w400,
      letterSpacing: 0.25,
      height: 1.43,
    ),
    'bodySmall': TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w400,
      letterSpacing: 0.4,
      height: 1.33,
    ),
    'labelLarge': TextStyle(
      fontSize: 14,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.1,
      height: 1.43,
    ),
    'labelMedium': TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.5,
      height: 1.33,
    ),
    'labelSmall': TextStyle(
      fontSize: 11,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.5,
      height: 1.45,
    ),
  };

  // ──────────────────────────────────────────────
  // ELEVACIÓN / SOMBRAS
  // ──────────────────────────────────────────────
  static const List<BoxShadow> elevation1 = [
    BoxShadow(
      color: Color(0x1A000000),
      blurRadius: 4,
      offset: Offset(0, 1),
    ),
  ];

  static const List<BoxShadow> elevation2 = [
    BoxShadow(
      color: Color(0x1A000000),
      blurRadius: 8,
      offset: Offset(0, 2),
    ),
  ];

  static const List<BoxShadow> elevation3 = [
    BoxShadow(
      color: Color(0x1A000000),
      blurRadius: 16,
      offset: Offset(0, 4),
    ),
  ];

  static const List<BoxShadow> elevation4 = [
    BoxShadow(
      color: Color(0x1A000000),
      blurRadius: 24,
      offset: Offset(0, 8),
    ),
  ];

  // ──────────────────────────────────────────────
  // DURACIONES DE ANIMACIÓN
  // ──────────────────────────────────────────────
  static const Duration durationFast = Duration(milliseconds: 150);
  static const Duration durationNormal = Duration(milliseconds: 250);
  static const Duration durationSlow = Duration(milliseconds: 350);

  // ──────────────────────────────────────────────
  // BREAKPOINTS RESPONSIVOS
  // ──────────────────────────────────────────────
  static const double breakpointMobile = 600;
  static const double breakpointTablet = 900;
  static const double breakpointDesktop = 1200;
  static const double breakpointWide = 1536;

  // ──────────────────────────────────────────────
  // HELPERS DE ACCESO RÁPIDO
  // ──────────────────────────────────────────────

  static double space(String key) => spacing[key] ?? 16;
  static double rad(String key) => radius[key] ?? 10;
  static TextStyle style(String key) => textStyles[key] ?? textStyles['bodyMedium']!;

  // Métodos de conveniencia
  static EdgeInsets paddingAll(String key) => EdgeInsets.all(space(key));
  static EdgeInsets paddingSymmetric({String h = 'md', String v = 'md'}) =>
      EdgeInsets.symmetric(horizontal: space(h), vertical: space(v));
  static EdgeInsets paddingOnly({
    String left = 'none',
    String top = 'none',
    String right = 'none',
    String bottom = 'none',
  }) =>
      EdgeInsets.only(
        left: space(left),
        top: space(top),
        right: space(right),
        bottom: space(bottom),
      );

  static BorderRadius borderRadius(String key) => BorderRadius.circular(rad(key));
  static BorderRadius borderRadiusOnly({
    String topLeft = 'none',
    String topRight = 'none',
    String bottomLeft = 'none',
    String bottomRight = 'none',
  }) =>
      BorderRadius.only(
        topLeft: Radius.circular(rad(topLeft)),
        topRight: Radius.circular(rad(topRight)),
        bottomLeft: Radius.circular(rad(bottomLeft)),
        bottomRight: Radius.circular(rad(bottomRight)),
      );
}

/// Extensión para acceso fácil desde BuildContext
extension DesignTokensExt on BuildContext {
  Color get primary => DesignTokens.primary;
  Color get primaryLight => DesignTokens.primaryLight;
  Color get primaryDark => DesignTokens.primaryDark;
  Color get background => DesignTokens.background;
  Color get surface => DesignTokens.surface;
  Color get surfaceVariant => DesignTokens.surfaceVariant;
  Color get text => DesignTokens.text;
  Color get textSecondary => DesignTokens.textSecondary;
  Color get textMuted => DesignTokens.textMuted;
  Color get border => DesignTokens.border;
  Color get borderStrong => DesignTokens.borderStrong;
  Color get error => DesignTokens.error;
  Color get success => DesignTokens.success;
  Color get warning => DesignTokens.warning;
  Color get info => DesignTokens.info;

  double space(String key) => DesignTokens.space(key);
  double rad(String key) => DesignTokens.rad(key);
  TextStyle style(String key) => DesignTokens.style(key);

  double get spaceXs => DesignTokens.spaceXs;
  double get spaceSm => DesignTokens.spaceSm;
  double get spaceMd => DesignTokens.spaceMd;
  double get spaceLg => DesignTokens.spaceLg;
  double get spaceXl => DesignTokens.spaceXl;

  double get radiusSm => DesignTokens.radiusSm;
  double get radiusMd => DesignTokens.radiusMd;
  double get radiusLg => DesignTokens.radiusLg;
  double get radiusXl => DesignTokens.radiusXl;

  TextStyle get displayLarge => DesignTokens.style('displayLarge');
  TextStyle get displayMedium => DesignTokens.style('displayMedium');
  TextStyle get displaySmall => DesignTokens.style('displaySmall');
  TextStyle get headlineLarge => DesignTokens.style('headlineLarge');
  TextStyle get headlineMedium => DesignTokens.style('headlineMedium');
  TextStyle get headlineSmall => DesignTokens.style('headlineSmall');
  TextStyle get titleLarge => DesignTokens.style('titleLarge');
  TextStyle get titleMedium => DesignTokens.style('titleMedium');
  TextStyle get titleSmall => DesignTokens.style('titleSmall');
  TextStyle get bodyLarge => DesignTokens.style('bodyLarge');
  TextStyle get bodyMedium => DesignTokens.style('bodyMedium');
  TextStyle get bodySmall => DesignTokens.style('bodySmall');
  TextStyle get labelLarge => DesignTokens.style('labelLarge');
  TextStyle get labelMedium => DesignTokens.style('labelMedium');
  TextStyle get labelSmall => DesignTokens.style('labelSmall');

  // Breakpoints
  bool get isMobile => MediaQuery.of(this).size.width < DesignTokens.breakpointMobile;
  bool get isTablet => MediaQuery.of(this).size.width >= DesignTokens.breakpointMobile &&
      MediaQuery.of(this).size.width < DesignTokens.breakpointDesktop;
  bool get isDesktop => MediaQuery.of(this).size.width >= DesignTokens.breakpointDesktop;
  bool get isWide => MediaQuery.of(this).size.width >= DesignTokens.breakpointWide;

  // Padding helpers
  EdgeInsets paddingAll(String key) => DesignTokens.paddingAll(key);
  EdgeInsets paddingSymmetric({String h = 'md', String v = 'md'}) =>
      DesignTokens.paddingSymmetric(h: h, v: v);
}
