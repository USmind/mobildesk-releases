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

/// Diálogo de advertencia
Future<void> showWarningDialog(
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
          Icon(Icons.warning_amber_rounded, color: DesignTokens.warning, size: 28),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold))),
        ],
      ),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('Cancelar'),
        ),
        if (actionLabel != null && onAction != null)
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              onAction();
            },
            style: FilledButton.styleFrom(backgroundColor: DesignTokens.warning),
            child: Text(actionLabel),
          ),
      ],
    ),
  );
}

/// Diálogo de información
Future<void> showInfoDialog(
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
          Icon(Icons.info_outline_rounded, color: DesignTokens.primary, size: 28),
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

/// Bottom sheet de acción (para móviles)
Future<T?> showActionSheet<T>(
  BuildContext context, {
  required String title,
  required List<ActionSheetItem<T>> items,
  String? cancelLabel,
}) {
  return showModalBottomSheet<T>(
    context: context,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(DesignTokens.radius['xl']!)),
    ),
    builder: (ctx) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: DesignTokens.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
          const Divider(height: 1),
          ...items.map((item) => ListTile(
            leading: item.icon != null ? Icon(item.icon, color: item.color) : null,
            title: Text(item.label, style: TextStyle(
              color: item.color,
              fontWeight: item.isDestructive ? FontWeight.bold : FontWeight.normal,
            )),
            onTap: () => Navigator.pop(ctx, item.value),
          )),
          if (cancelLabel != null) ...[
            const Divider(height: 1),
            ListTile(
              title: Text(cancelLabel, style: const TextStyle(color: DesignTokens.textMuted)),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ],
      ),
    ),
  );
}

class ActionSheetItem<T> {
  final String label;
  final T value;
  final IconData? icon;
  final Color? color;
  final bool isDestructive;

  const ActionSheetItem({
    required this.label,
    required this.value,
    this.icon,
    this.color,
    this.isDestructive = false,
  });
}