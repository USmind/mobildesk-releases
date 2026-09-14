/// Utilidades responsivas para MobilDesk App
/// Breakpoints y helpers para layouts adaptativos

import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';

/// Breakpoints estándar de la app
class AppBreakpoints {
  static const double mobile = DesignTokens.breakpointMobile;      // < 600
  static const double tablet = DesignTokens.breakpointTablet;      // 600 - 900
  static const double desktop = DesignTokens.breakpointDesktop;    // 900 - 1200
  static const double wide = DesignTokens.breakpointWide;          // > 1200

  static bool isMobile(BuildContext ctx) =>
      MediaQuery.of(ctx).size.width < mobile;

  static bool isTablet(BuildContext ctx) =>
      MediaQuery.of(ctx).size.width >= mobile &&
      MediaQuery.of(ctx).size.width < desktop;

  static bool isDesktop(BuildContext ctx) =>
      MediaQuery.of(ctx).size.width >= desktop;

  static bool isWide(BuildContext ctx) =>
      MediaQuery.of(ctx).size.width >= wide;
}

/// Widget que cambia según breakpoint
class ResponsiveBuilder extends StatelessWidget {
  final Widget Function(BuildContext, BoxConstraints) mobile;
  final Widget Function(BuildContext, BoxConstraints)? tablet;
  final Widget Function(BuildContext, BoxConstraints)? desktop;

  const ResponsiveBuilder({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= AppBreakpoints.desktop && desktop != null) {
          return desktop!(context, constraints);
        }
        if (constraints.maxWidth >= AppBreakpoints.tablet && tablet != null) {
          return tablet!(context, constraints);
        }
        return mobile(context, constraints);
      },
    );
  }
}

/// Valor responsivo según breakpoint
class ResponsiveValue<T> {
  final T mobile;
  final T? tablet;
  final T? desktop;

  const ResponsiveValue({
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  T resolve(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width >= AppBreakpoints.desktop && desktop != null) return desktop!;
    if (width >= AppBreakpoints.tablet && tablet != null) return tablet!;
    return mobile;
  }
}

/// Extension para acceso fácil
extension ResponsiveExt on BuildContext {
  T responsiveValue<T>(ResponsiveValue<T> value) => value.resolve(this);
}

/// Grid responsivo que se adapta automáticamente
class ResponsiveGrid extends StatelessWidget {
  final List<Widget> children;
  final ResponsiveValue<double> itemWidth;
  final ResponsiveValue<double> spacing;
  final ResponsiveValue<double> runSpacing;
  final int? maxItemsPerRow;

  const ResponsiveGrid({
    super.key,
    required this.children,
    required this.itemWidth,
    this.spacing = const ResponsiveValue(mobile: 12),
    this.runSpacing = const ResponsiveValue(mobile: 12),
    this.maxItemsPerRow,
  });

  @override
  Widget build(BuildContext context) {
    final w = itemWidth.resolve(context);
    final s = spacing.resolve(context);
    final rs = runSpacing.resolve(context);

    return Wrap(
      spacing: s,
      runSpacing: rs,
      children: children
          .map((child) => SizedBox(width: w, child: child))
          .toList(),
    );
  }
}

/// ListView/GridView responsivo
class ResponsiveListView extends StatelessWidget {
  final List<Widget> children;
  final ResponsiveValue<int> crossAxisCount;
  final ResponsiveValue<double> spacing;
  final ResponsiveValue<double> runSpacing;
  final double childAspectRatio;
  final bool shrinkWrap;
  final ScrollPhysics? physics;

  const ResponsiveListView({
    super.key,
    required this.children,
    required this.crossAxisCount,
    this.spacing = const ResponsiveValue(mobile: 12),
    this.runSpacing = const ResponsiveValue(mobile: 12),
    this.childAspectRatio = 1.0,
    this.shrinkWrap = false,
    this.physics,
  });

  @override
  Widget build(BuildContext context) {
    final crossAxis = crossAxisCount.resolve(context);
    final s = spacing.resolve(context);
    final rs = runSpacing.resolve(context);

    if (crossAxis == 1) {
      return ListView.separated(
        shrinkWrap: shrinkWrap,
        physics: physics,
        itemCount: children.length,
        separatorBuilder: (_, __) => SizedBox(height: s),
        itemBuilder: (_, i) => children[i],
      );
    }

    return GridView.count(
      shrinkWrap: shrinkWrap,
      physics: physics,
      crossAxisCount: crossAxis,
      mainAxisSpacing: rs,
      crossAxisSpacing: s,
      childAspectRatio: childAspectRatio,
      children: children,
    );
  }
}

/// Padding responsivo
class ResponsivePadding extends StatelessWidget {
  final Widget child;
  final ResponsiveValue<EdgeInsets> padding;

  const ResponsivePadding({
    super.key,
    required this.child,
    required this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(padding: padding.resolve(context), child: child);
  }
}

/// Padding simétrico responsivo
class ResponsiveSymmetricPadding extends StatelessWidget {
  final Widget child;
  final ResponsiveValue<double> horizontal;
  final ResponsiveValue<double> vertical;

  const ResponsiveSymmetricPadding({
    super.key,
    required this.child,
    required this.horizontal,
    required this.vertical,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: horizontal.resolve(context),
        vertical: vertical.resolve(context),
      ),
      child: child,
    );
  }
}

/// Tamaño de fuente responsivo
class ResponsiveText extends StatelessWidget {
  final String data;
  final ResponsiveValue<double> fontSize;
  final FontWeight? fontWeight;
  final Color? color;
  final TextAlign? textAlign;
  final int? maxLines;
  final TextOverflow? overflow;
  final TextStyle? style;

  const ResponsiveText(
    this.data, {
    super.key,
    required this.fontSize,
    this.fontWeight,
    this.color,
    this.textAlign,
    this.maxLines,
    this.overflow,
    this.style,
  });

  @override
  Widget build(BuildContext context) {
    return Text(
      data,
      style: (style ?? const TextStyle()).copyWith(
        fontSize: fontSize.resolve(context),
        fontWeight: fontWeight,
        color: color,
      ),
      textAlign: textAlign,
      maxLines: maxLines,
      overflow: overflow,
    );
  }
}

/// Column/Row responsivo que cambia dirección
class ResponsiveFlex extends StatelessWidget {
  final List<Widget> children;
  final ResponsiveValue<Axis> direction;
  final MainAxisAlignment mainAxisAlignment;
  final CrossAxisAlignment crossAxisAlignment;
  final ResponsiveValue<double> spacing;

  const ResponsiveFlex({
    super.key,
    required this.children,
    required this.direction,
    this.mainAxisAlignment = MainAxisAlignment.start,
    this.crossAxisAlignment = CrossAxisAlignment.start,
    this.spacing = const ResponsiveValue(mobile: 12),
  });

  @override
  Widget build(BuildContext context) {
    final dir = direction.resolve(context);
    final s = spacing.resolve(context);

    final widgets = <Widget>[];
    for (int i = 0; i < children.length; i++) {
      widgets.add(children[i]);
      if (i < children.length - 1) {
        widgets.add(SizedBox(
          width: dir == Axis.horizontal ? s : 0,
          height: dir == Axis.vertical ? s : 0,
        ));
      }
    }

    return dir == Axis.horizontal
        ? Row(
            mainAxisAlignment: mainAxisAlignment,
            crossAxisAlignment: crossAxisAlignment,
            children: widgets,
          )
        : Column(
            mainAxisAlignment: mainAxisAlignment,
            crossAxisAlignment: crossAxisAlignment,
            children: widgets,
          );
  }
}

/// Helper para crear ResponsiveValue fácilmente
ResponsiveValue<T> rv<T>({
  required T mobile,
  T? tablet,
  T? desktop,
}) =>
    ResponsiveValue<T>(mobile: mobile, tablet: tablet, desktop: desktop);

/// Extension para usar double como SizedBox
extension SizedBoxExtension on double {
  SizedBox get width => SizedBox(width: this);
  SizedBox get height => SizedBox(height: this);
}