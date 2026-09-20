import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/design_tokens.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';

class LoginScreen extends StatefulWidget {
  final AppState appState;
  const LoginScreen({super.key, required this.appState});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _codeController = TextEditingController();
  bool _isLoading = false;

  Future<void> _handleCodeConnect() async {
    final code = _codeController.text.trim().toUpperCase();
    if (code.isEmpty) {
      showErrorDialog(
        context,
        title: 'Código requerido',
        message: 'Por favor escribe el Código de tu Negocio.',
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      await widget.appState.connectWithBusinessCode(code);
    } catch (e) {
      if (mounted) {
        showErrorDialog(
          context,
          title: 'Error de conexión',
          message: e.toString().replaceAll('Exception:', '').trim(),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DesignTokens.background,
      body: Center(
        child: SingleChildScrollView(
          padding: DesignTokens.paddingSymmetric(h: 'xl', v: '2xl'),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Logo
                Center(
                  child: ClipRRect(
                    borderRadius: DesignTokens.borderRadius('lg'),
                    child: Image.asset(
                      'assets/logo.png',
                      width: 84,
                      height: 84,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        width: 84,
                        height: 84,
                        decoration: BoxDecoration(
                          color: DesignTokens.primaryContainer,
                          borderRadius: DesignTokens.borderRadius('lg'),
                        ),
                        child: Icon(Icons.store_rounded, size: 48, color: DesignTokens.primary),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'MOBILDESK MÓVIL',
                  textAlign: TextAlign.center,
                  style: DesignTokens.style('headlineMedium').copyWith(
                    fontWeight: FontWeight.w800,
                    color: DesignTokens.text,
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Punto de Venta e Inventario en Tiempo Real',
                  textAlign: TextAlign.center,
                  style: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textMuted),
                ),
                const SizedBox(height: 32),

                // Card de Enlace
                Card(
                  elevation: 0,
                  color: DesignTokens.surface,
                  surfaceTintColor: Colors.transparent,
                  shape: RoundedRectangleBorder(
                    borderRadius: DesignTokens.borderRadius('xl'),
                    side: BorderSide(color: DesignTokens.border, width: 1),
                  ),
                  margin: EdgeInsets.zero,
                  child: Padding(
                    padding: DesignTokens.paddingAll('xl'),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Enlazar con tu Negocio',
                          style: DesignTokens.style('titleLarge').copyWith(
                            fontWeight: FontWeight.bold,
                            color: DesignTokens.text,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Ingresa el Código de Negocio que aparece en la computadora para sincronizar productos, precios, tasa del dólar y ventas:',
                          style: DesignTokens.style('bodySmall').copyWith(
                            color: DesignTokens.textMuted,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 20),
                        TextField(
                          controller: _codeController,
                          textCapitalization: TextCapitalization.characters,
                          style: DesignTokens.style('bodyLarge').copyWith(
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                          decoration: InputDecoration(
                            labelText: 'Código de Negocio',
                            hintText: 'Ej: BODEGA-1234',
                            prefixIcon: Icon(Icons.key_rounded, color: DesignTokens.primary),
                          ),
                        ),
                        const SizedBox(height: 22),
                        FilledButton(
                          onPressed: _isLoading ? null : _handleCodeConnect,
                          style: FilledButton.styleFrom(
                            backgroundColor: DesignTokens.success,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: DesignTokens.borderRadius('lg'),
                            ),
                            elevation: 0,
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  height: 22,
                                  width: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.5,
                                    color: DesignTokens.textOnPrimary,
                                  ),
                                )
                              : Text(
                                  'Conectar Negocio',
                                  style: DesignTokens.style('labelLarge').copyWith(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  '¿No tienes código? En la PC ve a Configuración → Mi Código',
                  textAlign: TextAlign.center,
                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: () async {
                    final uri = Uri.parse('https://github.com/USmind/mobildesk-releases/releases/latest');
                    if (await canLaunchUrl(uri)) {
                      await launchUrl(uri, mode: LaunchMode.externalApplication);
                    }
                  },
                  icon: Icon(Icons.download_rounded, size: 18, color: DesignTokens.primary),
                  label: Text('¿Solo tienes la App? Descargar programa para PC', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.primary, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}