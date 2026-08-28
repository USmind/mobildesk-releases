import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

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
        if (last != null && now.difference(last).inMilliseconds < 1500) {
          continue; // Cooldown de 1.5s para el mismo código exacto
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
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: Colors.white, size: 48),
              const SizedBox(height: 16),
              Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(
                message,
                style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 13),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    style: OutlinedButton.styleFrom(foregroundColor: Colors.white, side: const BorderSide(color: Colors.white24)),
                    child: const Text('Cerrar'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton(
                    onPressed: () {
                      setState(() => _handled = false);
                      _controller.start();
                    },
                    style: FilledButton.styleFrom(backgroundColor: const Color(0xFF2563EB)),
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
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: Colors.white,
        title: Text(widget.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        actions: [
          IconButton(
            tooltip: _isMultiScan ? 'Modo Múltiple Activo' : 'Modo Individual',
            icon: Icon(
              _isMultiScan ? Icons.filter_none_rounded : Icons.crop_portrait_rounded,
              color: _isMultiScan ? const Color(0xFF38BDF8) : Colors.white70,
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
                border: Border.all(color: _isMultiScan ? const Color(0xFF38BDF8) : Colors.white, width: 2.5),
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(
                    color: (_isMultiScan ? const Color(0xFF38BDF8) : Colors.white).withValues(alpha: 0.15),
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
                if (_isMultiScan && _scannedCodes.isNotEmpty) ...[
                  Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F172A).withValues(alpha: 0.92),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF38BDF8), width: 1.5),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle_rounded, color: Color(0xFF4ADE80), size: 20),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Último: ${_lastCode ?? ""}',
                            style: const TextStyle(color: Colors.white, fontSize: 13.5, fontWeight: FontWeight.w600),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF2563EB),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '${_scannedCodes.length} items',
                            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton.icon(
                      onPressed: _finishMultiScan,
                      icon: const Icon(Icons.shopping_cart_checkout_rounded, size: 20),
                      label: Text('Listo · Cargar ${_scannedCodes.length} Productos', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF16A34A),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 4,
                      ),
                    ),
                  ),
                ] else ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.75),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _isMultiScan ? Icons.all_inclusive_rounded : Icons.qr_code_scanner_rounded,
                          color: _isMultiScan ? const Color(0xFF38BDF8) : Colors.white70,
                          size: 22,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _isMultiScan
                                ? 'Modo Ráfaga: Apunta a varios productos seguidos'
                                : 'Apunta la cámara al código de barras del producto',
                            style: const TextStyle(color: Colors.white, fontSize: 13),
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
