import 'package:flutter/material.dart';
import '../services/app_state.dart';

class LicenseBlockedScreen extends StatelessWidget {
  final AppState state;
  const LicenseBlockedScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        // Si la licencia se renueva en el PC y llega por sincronizacion,
        // esta pantalla desaparece sola.
        if (!state.licenciaBloqueada) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('✅ Licencia válida — aplicación desbloqueada.'),
                  backgroundColor: Color(0xFF059669),
                ),
              );
            }
          });
        }
        final esDemoLocal = state.licEstado == 'desconocida';
        final titulo = esDemoLocal
            ? 'Tu período de prueba terminó'
            : 'Licencia expirada';
        final mensaje = esDemoLocal
            ? 'Los 7 días de prueba de la aplicación han terminado.\n\nActiva tu licencia en el programa MobilDesk POS de tu computadora: la app se desbloqueará automáticamente al sincronizar.'
            : 'La licencia de MobilDesk POS ha expirado.\n\nRenueva o activa tu licencia en el programa de la computadora: la app se desbloqueará automáticamente al sincronizar.';

        return Scaffold(
          backgroundColor: const Color(0xFF0F172A),
          body: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        color: const Color(0xFFDC2626).withValues(alpha: 0.12),
                        shape: BoxShape.circle,
                        border: Border.all(color: const Color(0xFFDC2626), width: 2),
                      ),
                      child: const Icon(Icons.lock_rounded, color: Color(0xFFDC2626), size: 52),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      titulo,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      mensaje,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 14, height: 1.5),
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFF334155)),
                      ),
                      child: Text(
                        'Tiempo restante: ${state.licenciaRestanteTexto}',
                        style: const TextStyle(color: Color(0xFFFCA5A5), fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(height: 28),
                    FilledButton.icon(
                      onPressed: state.isSyncing ? null : state.sync,
                      icon: state.isSyncing
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.sync_rounded),
                      label: Text(state.isSyncing ? 'Sincronizando...' : 'Reintentar sincronización'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text(
                      'MobilDesk POS · Multi-Dispositivo',
                      style: TextStyle(color: Color(0xFF475569), fontSize: 12),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
