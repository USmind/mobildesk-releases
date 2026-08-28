import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/app_state.dart';

class SettingsScreen extends StatefulWidget {
  final AppState state;
  const SettingsScreen({super.key, required this.state});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _nameController;
  late TextEditingController _rateController;
  late TextEditingController _marginController;
  late TextEditingController _businessIdController;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.state.businessName);
    _rateController = TextEditingController(text: widget.state.exchangeRate.toStringAsFixed(2));
    _marginController = TextEditingController(text: widget.state.profitMargin.toStringAsFixed(0));
    _businessIdController = TextEditingController(text: widget.state.businessId ?? '');
  }

  bool _checkingUpdate = false;

  List<int> _parseVersion(String v) {
    final clean = v.trim().toLowerCase().replaceAll(RegExp(r'^v'), '');
    return clean.split('.').map((p) => int.tryParse(RegExp(r'\d+').firstMatch(p)?.group(0) ?? '0') ?? 0).toList();
  }

  bool _isNewer(String remote, String current) {
    final r = _parseVersion(remote);
    final c = _parseVersion(current);
    for (int i = 0; i < r.length || i < c.length; i++) {
      final rv = i < r.length ? r[i] : 0;
      final cv = i < c.length ? c[i] : 0;
      if (rv > cv) return true;
      if (rv < cv) return false;
    }
    return false;
  }

  Future<void> _checkForUpdate() async {
    if (_checkingUpdate) return;
    setState(() => _checkingUpdate = true);
    try {
      final info = await PackageInfo.fromPlatform();
      final current = info.version;
      final data = await widget.state.checkAppUpdate();
      if (data == null) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo conectar con el servidor de actualizaciones. Verifica tu conexión a Internet.')),
        );
        return;
      }
      final remote = (data['mobile_version'] ?? data['version'] ?? '').toString();
      final url = (data['mobile_download_url'] ?? data['download_url'] ?? '').toString();
      final changelog = (data['mobile_changelog'] ?? data['changelog'] ?? '').toString();
      if (remote.isEmpty || !_isNewer(remote, current)) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Ya tienes la última versión ($current).')),
        );
        return;
      }
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Actualización disponible: v$remote'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Versión instalada: $current', style: const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
                const SizedBox(height: 8),
                Text(changelog.isNotEmpty ? changelog : 'Mejoras y correcciones.'),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Más tarde')),
            FilledButton(
              onPressed: () async {
                Navigator.pop(ctx);
                if (url.isNotEmpty) {
                  try {
                    final uri = Uri.parse(url);
                    final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
                    if (!ok && mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('No se pudo abrir el navegador. Copia el enlace manualmente.')),
                      );
                    }
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('No se pudo abrir el navegador. Verifica tu conexión e intenta de nuevo.')),
                      );
                    }
                  }
                }
              },
              child: const Text('Descargar'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error al verificar actualización: $e')));
    } finally {
      if (mounted) setState(() => _checkingUpdate = false);
    }
  }

  void _saveSettings() {
    final name = _nameController.text.trim();
    final rate = double.tryParse(_rateController.text.replaceAll(',', '.')) ?? widget.state.exchangeRate;
    final margin = double.tryParse(_marginController.text.replaceAll(',', '.')) ?? widget.state.profitMargin;
    final bid = _businessIdController.text.trim();

    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('El nombre del negocio no puede estar vacío.')),
      );
      return;
    }

    widget.state.updateSettings(
      name: name,
      rate: rate,
      margin: margin,
      customBusinessId: bid.isNotEmpty ? bid : null,
    );
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Configuración guardada correctamente.')),
    );
    widget.state.sync();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: const Text('Configuración y Cuenta', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Store settings card
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE2E8F0)),
            ),
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Datos del Comercio', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Nombre del Negocio',
                      prefixIcon: Icon(Icons.storefront_rounded),
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _rateController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(
                            labelText: 'Tasa USD/Bs',
                            prefixIcon: Icon(Icons.currency_exchange_rounded),
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _marginController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(
                            labelText: '% Ganancia',
                            prefixIcon: Icon(Icons.percent_rounded),
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _saveSettings,
                      icon: const Icon(Icons.save_rounded),
                      label: const Text('Guardar Ajustes'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Sincronización
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE2E8F0)),
            ),
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Sincronización en la Nube', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                  const SizedBox(height: 8),
                  Text('Cuenta: ${widget.state.email ?? "Desconectado"}', style: const TextStyle(fontSize: 13, color: Color(0xFF64748B))),
                  const SizedBox(height: 4),
                  Text('Estado: ${widget.state.syncStatus}', style: const TextStyle(fontSize: 13, color: Color(0xFF0F766E), fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _businessIdController,
                    decoration: const InputDecoration(
                      labelText: 'ID del Negocio (Supabase)',
                      prefixIcon: Icon(Icons.vpn_key_outlined),
                      border: OutlineInputBorder(),
                      helperText: 'Debe coincidir con el Negocio ID del PC',
                    ),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: widget.state.isSyncing ? null : widget.state.sync,
                          icon: widget.state.isSyncing
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.sync_rounded),
                          label: Text(widget.state.isSyncing ? 'Sincronizando...' : 'Sincronizar Ahora'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      FilledButton(
                        onPressed: _saveSettings,
                        style: FilledButton.styleFrom(backgroundColor: const Color(0xFF0F766E)),
                        child: const Text('Actualizar ID'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Licencia (sincronizada con el PC)
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(
                color: widget.state.licenciaBloqueada ? const Color(0xFFFECACA) : const Color(0xFFE2E8F0),
              ),
            ),
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        widget.state.licenciaBloqueada ? Icons.lock_rounded : Icons.verified_rounded,
                        color: widget.state.licenciaBloqueada ? const Color(0xFFDC2626) : const Color(0xFF059669),
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      const Text('Licencia', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text('Estado: ${widget.state.licenciaEstadoTexto}', style: const TextStyle(fontSize: 13, color: Color(0xFF334155))),
                  const SizedBox(height: 4),
                  Text(
                    'Tiempo restante: ${widget.state.licenciaRestanteTexto}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: widget.state.licenciaBloqueada ? const Color(0xFFDC2626) : const Color(0xFF0F766E),
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Sincronizada con el programa de la PC: mismos días y horas restantes. Se activa desde el programa de la computadora.',
                    style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Actualizaciones
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE2E8F0)),
            ),
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Actualizar aplicación', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B))),
                  const SizedBox(height: 6),
                  const Text('Verifica si hay una nueva versión con mejoras.', style: TextStyle(fontSize: 13, color: Color(0xFF64748B))),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _checkingUpdate ? null : _checkForUpdate,
                      icon: _checkingUpdate
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.system_update_rounded),
                      label: Text(_checkingUpdate ? 'Verificando...' : 'Buscar actualizaciones'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF0F172A),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Logout
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFFEE2E2)),
            ),
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Cerrar Sesión', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFDC2626))),
                  const SizedBox(height: 6),
                  const Text(
                    'Si deseas cambiar de cuenta o re-enlazar desde cero, pulsa cerrar sesión.',
                    style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: widget.state.logout,
                      icon: const Icon(Icons.logout_rounded),
                      label: const Text('Cerrar Sesión'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFFDC2626),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
