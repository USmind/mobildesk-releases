import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';
import '../services/app_state.dart';

class SettingsScreen extends StatefulWidget {
  final AppState state;
  const SettingsScreen({super.key, required this.state});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _nameCtrl = TextEditingController();
  final _rateCtrl = TextEditingController();
  final _marginCtrl = TextEditingController();
  final _bidCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _nameCtrl.text = widget.state.businessName;
    _rateCtrl.text = widget.state.exchangeRate.toStringAsFixed(2);
    _marginCtrl.text = widget.state.profitMargin.toStringAsFixed(0);
    _bidCtrl.text = widget.state.businessId ?? '';
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _rateCtrl.dispose();
    _marginCtrl.dispose();
    _bidCtrl.dispose();
    super.dispose();
  }

  void _save() {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El nombre del negocio no puede estar vacío.')),
      );
      return;
    }
    final rate = double.tryParse(_rateCtrl.text.replaceAll(',', '.')) ?? widget.state.exchangeRate;
    final margin = double.tryParse(_marginCtrl.text.replaceAll(',', '.')) ?? widget.state.profitMargin;
    final bid = _bidCtrl.text.trim();
    widget.state.updateSettings(
      name: name,
      rate: rate,
      margin: margin,
      customBusinessId: bid.isNotEmpty ? bid : null,
    );
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Configuración guardada correctamente.')),
    );
  }

  Future<void> _checkForUpdate() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Buscando actualizaciones...')),
    );
    final info = await widget.state.checkForUpdate();
    if (!mounted) return;
    if (info == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tu app está actualizada.')),
      );
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Nueva versión v${info['version']}'),
        content: Text(
          'Versión actual: v${info['current_version']}\n\n'
          'Novedades:\n${info['changelog']}\n\n'
          'Se descargará el APK y el sistema te pedirá instalarlo.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Descargar')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    String? apkPath;
    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          widget.state.downloadApk(info['download_url'], (percent, downloaded, total) {
            setDialogState(() {});
          }).then((path) {
            apkPath = path;
            if (ctx.mounted) Navigator.pop(ctx);
          });
          return AlertDialog(
            title: const Text('Descargando actualización...'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const LinearProgressIndicator(),
                const SizedBox(height: 12),
                Text('Descargando APK...', style: DesignTokens.style('bodySmall')),
              ],
            ),
          );
        },
      ),
    );

    if (!mounted) return;
    if (apkPath == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Error al descargar la actualización.')),
        );
      }
      return;
    }

    final opened = await widget.state.openApkForInstall(apkPath!);
    if (!mounted) return;
    if (!opened) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo abrir el instalador. Instala el APK manualmente.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.state;
    final accent = DesignTokens.primary;
    final darkBg = DesignTokens.secondary;

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: darkBg,
        foregroundColor: Colors.white,
        title: Text(
          'Configuración y Cuenta',
          style: DesignTokens.style('titleLarge').copyWith(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _sectionTitle('Datos del Comercio', Icons.storefront_rounded),
          const SizedBox(height: 12),
          _field(_nameCtrl, 'Nombre del Negocio', Icons.storefront_rounded),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _field(_rateCtrl, 'Tasa USD/Bs', Icons.currency_exchange_rounded, isNum: true)),
              const SizedBox(width: 12),
              Expanded(child: _field(_marginCtrl, '% Ganancia', Icons.percent_rounded, isNum: true)),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: () async {
                final oldRate = s.exchangeRate;
                try {
                  await s.fetchBcvRateAndUpdate();
                } catch (_) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Sin conexión: no se pudo actualizar la tasa BCV.')),
                    );
                  }
                  return;
                }
                if (mounted) {
                  _rateCtrl.text = s.exchangeRate.toStringAsFixed(2);
                  final msg = s.exchangeRate != oldRate
                      ? 'Tasa BCV actualizada: 1 USD = Bs ${s.exchangeRate.toStringAsFixed(2)}'
                      : 'Sin conexión o tasa BCV sin cambios: 1 USD = Bs ${s.exchangeRate.toStringAsFixed(2)}';
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
                }
              },
              icon: const Icon(Icons.currency_exchange_rounded, size: 18),
              label: const Text('Actualizar desde BCV'),
            ),
          ),
          if (s.lastBcvUpdate != null && s.lastBcvUpdate!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'Última actualización BCV: ${s.lastBcvUpdate}',
                style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textMuted),
              ),
            ),
          const SizedBox(height: 16),
          _fullButton('Guardar Ajustes', Icons.save_rounded, accent, _save),
          const SizedBox(height: 24),

          _sectionTitle('Sincronización en la Nube', Icons.cloud_rounded),
          const SizedBox(height: 8),
          Text('Cuenta: ${s.email ?? "Desconectado"}', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
          const SizedBox(height: 4),
          Row(
            children: [
              Icon(Icons.circle, size: 8, color: s.syncStatus.contains('Sincronizado') ? DesignTokens.success : DesignTokens.warning),
              const SizedBox(width: 6),
              Expanded(
                child: Text(s.syncStatus, style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _field(_bidCtrl, 'ID del Negocio (Supabase)', Icons.vpn_key_outlined),
          Text('Debe coincidir con el Negocio ID del PC', style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textMuted)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: s.isSyncing ? null : s.sync,
                  icon: s.isSyncing
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.sync_rounded),
                  label: Text(s.isSyncing ? 'Sincronizando...' : 'Sincronizar'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _fullButton('Actualizar ID', Icons.check_rounded, DesignTokens.success, _save),
              ),
            ],
          ),
          const SizedBox(height: 24),

          _sectionTitle('Licencia', Icons.verified_rounded),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(
                s.licenciaBloqueada ? Icons.lock_rounded : Icons.verified_rounded,
                size: 16,
                color: s.licenciaBloqueada ? DesignTokens.error : DesignTokens.success,
              ),
              const SizedBox(width: 6),
              Text(s.licenciaEstadoTexto, style: DesignTokens.style('bodyMedium')),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Tiempo restante: ${s.licenciaRestanteTexto}',
            style: DesignTokens.style('bodySmall').copyWith(
              fontWeight: FontWeight.bold,
              color: s.licenciaBloqueada ? DesignTokens.error : DesignTokens.success,
            ),
          ),
          const SizedBox(height: 4),
          Text('Sincronizada con el programa de la PC.', style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textMuted)),
          const SizedBox(height: 24),

          _sectionTitle('Actualizar App', Icons.system_update_rounded),
          const SizedBox(height: 8),
          Text(
            'Busca nuevas versiones de MobilDesk en el servidor.',
            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
          ),
          const SizedBox(height: 12),
          _fullButton('Buscar Actualizaciones', Icons.download_rounded, DesignTokens.primary, _checkForUpdate),
          const SizedBox(height: 24),

          _sectionTitle('Cerrar Sesión', Icons.logout_rounded),
          const SizedBox(height: 8),
          Text(
            'Si deseas cambiar de cuenta o re-enlazar desde cero, pulsa cerrar sesión.',
            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
          ),
          const SizedBox(height: 12),
          _fullButton('Cerrar Sesión', Icons.logout_rounded, DesignTokens.error, s.logout),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 18, color: DesignTokens.primary),
        const SizedBox(width: 8),
        Text(text, style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.text)),
      ],
    );
  }

  Widget _field(TextEditingController ctrl, String label, IconData icon, {bool isNum = false}) {
    return TextField(
      controller: ctrl,
      keyboardType: isNum ? const TextInputType.numberWithOptions(decimal: true) : null,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
      ),
    );
  }

  Widget _fullButton(String label, IconData icon, Color color, VoidCallback onPressed) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 18),
        label: Text(label),
        style: FilledButton.styleFrom(backgroundColor: color),
      ),
    );
  }
}
