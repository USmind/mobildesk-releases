import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';

/// Estado de carga consistente
class LoadingState extends StatelessWidget {
  final String? message;
  final double size;
  final Color? color;

  const LoadingState({
    super.key,
    this.message,
    this.size = 40,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: size,
            height: size,
            child: CircularProgressIndicator(
              strokeWidth: 3,
              valueColor: AlwaysStoppedAnimation<Color>(color ?? DesignTokens.primary),
            ),
          ),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(
              message!,
              style: TextStyle(
                color: DesignTokens.textMuted,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }
}

/// Overlay de carga que bloquea la UI
class LoadingOverlay extends StatelessWidget {
  final bool isLoading;
  final String? message;
  final Widget child;

  const LoadingOverlay({
    super.key,
    required this.isLoading,
    this.message,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: Colors.black.withAlpha(80),
            child: LoadingState(message: message, size: 50),
          ),
      ],
    );
  }
}

/// Estado vacío consistente
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;
  final double iconSize;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.message,
    this.actionLabel,
    this.onAction,
    this.iconSize = 80,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: iconSize,
              height: iconSize,
              decoration: BoxDecoration(
                color: DesignTokens.primary.withAlpha(30),
                borderRadius: BorderRadius.circular(iconSize / 2),
              ),
              child: Icon(icon, size: iconSize * 0.5, color: DesignTokens.primary),
            ),
            const SizedBox(height: 20),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: DesignTokens.text,
              ),
              textAlign: TextAlign.center,
            ),
            if (message != null) ...[
              const SizedBox(height: 8),
              Text(
                message!,
                style: TextStyle(
                  fontSize: 14,
                  color: DesignTokens.textMuted,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.add_rounded),
                label: Text(actionLabel!),
                style: FilledButton.styleFrom(
                  backgroundColor: DesignTokens.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(DesignTokens.radius['md']!),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Estado de error consistente
class ErrorState extends StatelessWidget {
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;
  final IconData icon;

  const ErrorState({
    super.key,
    required this.title,
    this.message,
    this.actionLabel,
    this.onAction,
    this.icon = Icons.error_outline_rounded,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: DesignTokens.error.withAlpha(30),
                borderRadius: BorderRadius.circular(40),
              ),
              child: Icon(icon, size: 40, color: DesignTokens.error),
            ),
            const SizedBox(height: 20),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: DesignTokens.text,
              ),
              textAlign: TextAlign.center,
            ),
            if (message != null) ...[
              const SizedBox(height: 8),
              Text(
                message!,
                style: TextStyle(
                  fontSize: 14,
                  color: DesignTokens.textMuted,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.refresh_rounded),
                label: Text(actionLabel!),
                style: FilledButton.styleFrom(
                  backgroundColor: DesignTokens.error,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(DesignTokens.radius['md']!),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Widget que muestra estado según condición
class StateBuilder<T> extends StatelessWidget {
  final T? data;
  final bool isLoading;
  final String? error;
  final Widget Function(T data) builder;
  final Widget Function()? emptyBuilder;
  final Widget Function(String error, VoidCallback? retry)? errorBuilder;
  final Widget Function()? loadingBuilder;
  final VoidCallback? onRetry;

  const StateBuilder({
    super.key,
    required this.data,
    required this.isLoading,
    this.error,
    required this.builder,
    this.emptyBuilder,
    this.errorBuilder,
    this.loadingBuilder,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return loadingBuilder?.call() ?? const LoadingState(message: 'Cargando...');
    }

    if (error != null) {
      return errorBuilder?.call(error!, onRetry) ??
          ErrorState(
            title: 'Error',
            message: error,
            actionLabel: onRetry != null ? 'Reintentar' : null,
            onAction: onRetry,
          );
    }

    if (data == null) {
      return emptyBuilder?.call() ??
          const EmptyState(
            icon: Icons.inbox_outlined,
            title: 'No hay datos',
            message: 'No se encontraron resultados',
          );
    }

    return builder(data!);
  }
}

/// Pull-to-refresh wrapper
class RefreshableStateBuilder<T> extends StatelessWidget {
  final T? data;
  final bool isLoading;
  final String? error;
  final Widget Function(T data) builder;
  final Future<void> Function() onRefresh;
  final Widget Function()? emptyBuilder;
  final Widget Function(String error, VoidCallback? retry)? errorBuilder;
  final Widget Function()? loadingBuilder;

  const RefreshableStateBuilder({
    super.key,
    required this.data,
    required this.isLoading,
    this.error,
    required this.builder,
    required this.onRefresh,
    this.emptyBuilder,
    this.errorBuilder,
    this.loadingBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      color: DesignTokens.primary,
      child: StateBuilder<T>(
        data: data,
        isLoading: isLoading,
        error: error,
        builder: builder,
        emptyBuilder: emptyBuilder,
        errorBuilder: errorBuilder,
        loadingBuilder: loadingBuilder,
        onRetry: onRefresh,
      ),
    );
  }
}