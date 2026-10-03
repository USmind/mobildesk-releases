import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';

/// Diálogo de error - estilo consistente
Future<void> showErrorDialog(
  BuildContext context, {
  required String title,
  required String message,
  String? actionLabel,
  VoidCallback? onAction,
}) {
  return showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(DesignTokens.radius['lg']!)),
      title: Row(
        children: [
          Icon(Icons.error_outline_rounded, color: DesignTokens.error, size: 28),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold))),
        ],
      ),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('Entendido'),
        ),
        if (actionLabel != null && onAction != null)
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              onAction();
            },
            style: FilledButton.styleFrom(backgroundColor: DesignTokens.error),
            child: Text(actionLabel),
          ),
      ],
    ),
  );
}

/// Diálogo de éxito
Future<void> showSuccessDialog(
  BuildContext context, {
  required String title,
  required String message,
  String? actionLabel,
  VoidCallback? onAction,
}) {
  return showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(DesignTokens.radius['lg']!)),
      title: Row(
        children: [
          Icon(Icons.check_circle_outline_rounded, color: DesignTokens.success, size: 28),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold))),
        ],
      ),
      content: Text(message),
      actions: [
        FilledButton(
          onPressed: () {
            Navigator.pop(ctx);
            onAction?.call();
          },
          style: FilledButton.styleFrom(backgroundColor: DesignTokens.success),
          child: Text(actionLabel ?? 'Continuar'),
        ),
      ],
    ),
  );
}

/// Diálogo de confirmación
Future<bool> showConfirmDialog(
  BuildContext context, {
  required String title,
  required String message,
  String confirmLabel = 'Confirmar',
  String cancelLabel = 'Cancelar',
  bool isDestructive = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(DesignTokens.radius['lg']!)),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: Text(cancelLabel),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(ctx, true),
          style: FilledButton.styleFrom(
            backgroundColor: isDestructive ? DesignTokens.error : DesignTokens.primary,
          ),
          child: Text(confirmLabel),
        ),
      ],
    ),
  );
  return result ?? false;
}