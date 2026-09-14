import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../theme/design_tokens.dart';
import '../utils.dart';

class ScannerScreen extends StatefulWidget {
  final bool allowMultiScan;
  final String title;

  const ScannerScreen({
    super.key,
    this.allowMultiScan = false,
    this.title = 'Escanear código',
  });

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  late MobileScannerController _controller;
  bool _handled = false;
  late bool _isMultiScan;
  final List<String> _scannedCodes = [];
  final Map<String, DateTime> _lastScannedTime = {};
  String? _lastCode;

  @override
  void initState() {
    super.initState();
    _isMultiScan = widget.allowMultiScan;
    _controller = MobileScannerController(
      facing: CameraFacing.back,
      torchEnabled: false,
      detectionSpeed: DetectionSpeed.noDuplicates,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    final barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      final raw = barcode.rawValue;
      if (raw == null || raw.trim().isEmpty) continue;
      final code = raw.trim();

      if (!_isMultiScan) {
        if (_handled) return;
        _handled = true;
        HapticFeedback.mediumImpact();
        if (mounted) Navigator.pop(context, code);
        break;
      } else {
        final now = DateTime.now();
        final last = _lastScannedTime[code];
        if (last != null && now.difference(last).inMilliseconds < 600) {
          // Cooldown de 600ms para el mismo código exacto, con feedback.
          if (mounted) {
            ScaffoldMessenger.of(context)
              ..hideCurrentSnackBar()
              ..showSnackBar(
                SnackBar(
                  duration: const Duration(milliseconds: 500),
                  content: Text('Ya registrado: $code (espera un momento…)'),
                ),
              );
          }
          HapticFeedback.lightImpact();
          continue;
        }
        _lastScannedTime[code] = now;
        HapticFeedback.mediumImpact();

        setState(() {
          _scannedCodes.add(code);
          _lastCode = code;
        });
        break;
      }
    }
  }

  void _finishMultiScan() {
    if (mounted) {
      Navigator.pop(context, _scannedCodes);
    }
  }

  Map<String, int> get _groupedCounts {
    final map = <String, int>{};
    for (final c in _scannedCodes) {
      map[c] = (map[c] ?? 0) + 1;
    }
    return map;
  }

  void _removeOneCode(String code) {
    setState(() {
      final idx = _scannedCodes.lastIndexOf(code);
      if (idx >= 0) _scannedCodes.removeAt(idx);
      if (_scannedCodes.isEmpty) _lastCode = null;
    });
  }

  void _removeAllOfCode(String code) {
    setState(() {
      _scannedCodes.removeWhere((c) => c == code);
      if (_scannedCodes.isEmpty) _lastCode = null;
    });
  }

  Widget _errorBuilder(BuildContext context, MobileScannerException error) {
    final isPermissionDenied = error.errorCode == MobileScannerErrorCode.permissionDenied;
    final isUnsupported = error.errorCode == MobileScannerErrorCode.unsupported;

    String title;
    String message;
    IconData icon;

    if (isPermissionDenied) {
      title = 'Permiso de cámara denegado';
      message =
          'Para escanear códigos necesitas permitir el acceso a la cámara.\n\n'
          'Ve a Ajustes del teléfono → Aplicaciones → MobilDesk POS → Permisos → Cámara → Permitir.';
      icon = Icons.no_photography_rounded;
    } else if (isUnsupported) {
      title = 'Cámara no disponible';
      message = 'Este dispositivo no tiene cámara compatible o está siendo usada por otra app.';
      icon = Icons.videocam_off_rounded;
    } else {
      title = 'No se pudo iniciar la cámara';
      message = 'Intenta de nuevo. Si el problema persiste, reinicia la app.\n\nDetalle: ${error.errorCode.message}';
      if (error.errorDetails?.message != null) {
        message += '\n${error.errorDetails!.message}';
      }
      icon = Icons.error_outline_rounded;
    }

    return ColoredBox(
      color: Colors.black,
      child: Center(
        child: Padding(
          padding: DesignTokens.paddingAll('xl'),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: Colors.white, size: 48),
              DesignTokens.spaceLg.height,
              Text(
                title,
                style: DesignTokens.style('titleLarge').copyWith(color: Colors.white),
                textAlign: TextAlign.center,
              ),
              DesignTokens.spaceMd.height,
              Text(
                message,
                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.primaryLight),
                textAlign: TextAlign.center,
              ),
              DesignTokens.spaceLg.height,
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    style: OutlinedButton.styleFrom(foregroundColor: Colors.white, side: const BorderSide(color: Colors.white24)),
                    child: const Text('Cerrar'),
                  ),
                  DesignTokens.spaceMd.width,
                  FilledButton(
                    onPressed: () {
                      setState(() => _handled = false);
                      _controller.start();
                    },
                    style: FilledButton.styleFrom(backgroundColor: DesignTokens.primary),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondaryDark,
        foregroundColor: Colors.white,
        title: Text(widget.title, style: DesignTokens.style('titleLarge').copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            tooltip: _isMultiScan ? 'Modo Múltiple Activo' : 'Modo Individual',
            icon: Icon(
              _isMultiScan ? Icons.filter_none_rounded : Icons.crop_portrait_rounded,
              color: _isMultiScan ? DesignTokens.primary : Colors.white70,
            ),
            onPressed: () {
              setState(() {
                _isMultiScan = !_isMultiScan;
              });
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  duration: const Duration(seconds: 1),
                  content: Text(_isMultiScan ? 'Modo Ráfaga (Escaneo Múltiple) activado' : 'Modo Individual (1 código) activado'),
                ),
              );
            },
          ),
          IconButton(
            tooltip: 'Linterna',
            icon: ValueListenableBuilder(
              valueListenable: _controller,
              builder: (context, state, child) {
                final isOn = state.torchState == TorchState.on;
                return Icon(isOn ? Icons.flash_on_rounded : Icons.flash_off_rounded);
              },
            ),
            onPressed: () => _controller.toggleTorch(),
          ),
          IconButton(
            tooltip: 'Cambiar cámara',
            icon: const Icon(Icons.cameraswitch_rounded),
            onPressed: () => _controller.switchCamera(),
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
            errorBuilder: _errorBuilder,
          ),
          // Marco de escaneo
          Center(
            child: Container(
              width: 270,
              height: 170,
              decoration: BoxDecoration(
                border: Border.all(color: _isMultiScan ? DesignTokens.primary : Colors.white, width: 2.5),
                borderRadius: DesignTokens.borderRadius('lg'),
                boxShadow: [
                  BoxShadow(
                    color: (_isMultiScan ? DesignTokens.primary : Colors.white).withValues(alpha: 0.15),
                    blurRadius: 16,
                    spreadRadius: 2,
                  ),
                ],
              ),
            ),
          ),
          // Panel inferior de estado y control
          Positioned(
            bottom: 20,
            left: 16,
            right: 16,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_isMultiScan) ...[
                  Container(
                    margin: DesignTokens.paddingOnly(bottom: 'md'),
                    padding: DesignTokens.paddingSymmetric(h: 'lg', v: 'md'),
                    decoration: BoxDecoration(
                      color: DesignTokens.secondaryDark.withValues(alpha: 0.92),
                      borderRadius: DesignTokens.borderRadius('lg'),
                      border: Border.all(color: DesignTokens.primary, width: 1.5),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.check_circle_rounded, color: DesignTokens.success, size: 20),
                            DesignTokens.spaceMd.width,
                            Expanded(
                              child: Text(
                                _scannedCodes.isEmpty ? 'Sin códigos aún' : 'Último: ${_lastCode ?? ""}',
                                style: DesignTokens.style('bodyMedium').copyWith(color: Colors.white, fontWeight: FontWeight.w600),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Container(
                              padding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
                              decoration: BoxDecoration(
                                color: DesignTokens.primary,
                                borderRadius: DesignTokens.borderRadius('sm'),
                              ),
                              child: Text(
                                '${_scannedCodes.length} items · ${_groupedCounts.length} prod.',
                                style: DesignTokens.style('labelSmall').copyWith(color: Colors.white, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        if (_scannedCodes.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          ConstrainedBox(
                            constraints: const BoxConstraints(maxHeight: 140),
                            child: ListView(
                              shrinkWrap: true,
                              children: _groupedCounts.entries.map((e) => Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '${e.key}  ×${e.value}',
                                          style: DesignTokens.style('bodySmall').copyWith(color: Colors.white),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      IconButton(
                                        tooltip: 'Quitar uno',
                                        visualDensity: VisualDensity.compact,
                                        icon: const Icon(Icons.remove_circle_outline, color: Colors.white70, size: 20),
                                        onPressed: () => _removeOneCode(e.key),
                                      ),
                                      IconButton(
                                        tooltip: 'Quitar todos',
                                        visualDensity: VisualDensity.compact,
                                        icon: const Icon(Icons.delete_outline, color: Colors.white70, size: 20),
                                        onPressed: () => _removeAllOfCode(e.key),
                                      ),
                                    ],
                                  )).toList(),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton.icon(
                      onPressed: _scannedCodes.isEmpty ? null : _finishMultiScan,
                      icon: const Icon(Icons.shopping_cart_checkout_rounded, size: 20),
                      label: Text(
                        _scannedCodes.isEmpty
                            ? 'Terminar (sin códigos)'
                            : 'Terminar · Cargar ${_scannedCodes.length} Productos',
                        style: DesignTokens.style('titleSmall').copyWith(color: Colors.white),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: DesignTokens.success,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
                        elevation: 4,
                      ),
                    ),
                  ),
                ] else ...[
                  Container(
                    padding: DesignTokens.paddingSymmetric(h: 'lg', v: 'md'),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.75),
                      borderRadius: DesignTokens.borderRadius('lg'),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _isMultiScan ? Icons.all_inclusive_rounded : Icons.qr_code_scanner_rounded,
                          color: _isMultiScan ? DesignTokens.primary : Colors.white70,
                          size: 22,
                        ),
                        DesignTokens.spaceMd.width,
                        Expanded(
                          child: Text(
                            _isMultiScan
                                ? 'Modo Ráfaga: Apunta a varios productos seguidos'
                                : 'Apunta la cámara al código de barras del producto',
                            style: DesignTokens.style('bodySmall').copyWith(color: Colors.white),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
