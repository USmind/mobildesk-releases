import 'package:flutter/material.dart';
import '../models/models.dart';

class MixedPaymentDialog extends StatefulWidget {
  final double totalBs;
  final double totalUsd;
  final double tasa;
  final Function(PagoMixtoDetalle)? onConfirm;

  const MixedPaymentDialog({
    super.key,
    required this.totalBs,
    required this.totalUsd,
    required this.tasa,
    this.onConfirm,
  });

  @override
  State<MixedPaymentDialog> createState() => _MixedPaymentDialogState();
}

class _MixedPaymentDialogState extends State<MixedPaymentDialog> {
  final _usdCtrl = TextEditingController(text: '0.00');
  final _bsCtrl = TextEditingController(text: '0.00');
  final _pmCtrl = TextEditingController(text: '0.00');
  final _tarjetaCtrl = TextEditingController(text: '0.00');
  final _fiadoCtrl = TextEditingController(text: '0.00');

  late double _usdEnBs;
  late double _totalAbonado;
  late double _diferencia;

  @override
  void initState() {
    super.initState();
    _recalcular();
    for (final c in [_usdCtrl, _bsCtrl, _pmCtrl, _tarjetaCtrl, _fiadoCtrl]) {
      c.addListener(_recalcular);
    }
  }

  @override
  void dispose() {
    for (final c in [_usdCtrl, _bsCtrl, _pmCtrl, _tarjetaCtrl, _fiadoCtrl]) {
      c.removeListener(_recalcular);
      c.dispose();
    }
    super.dispose();
  }

  double _parse(String s) => double.tryParse(s.replaceAll(',', '.')) ?? 0;

  void _recalcular() {
    final usd = _parse(_usdCtrl.text);
    final bs = _parse(_bsCtrl.text);
    final pm = _parse(_pmCtrl.text);
    final tarjeta = _parse(_tarjetaCtrl.text);
    final fiado = _parse(_fiadoCtrl.text);

    setState(() {
      _usdEnBs = usd * widget.tasa;
      _totalAbonado = _usdEnBs + bs + pm + tarjeta + fiado;
      _diferencia = _totalAbonado - widget.totalBs;
    });
  }

  bool get _pagoCompleto => _diferencia >= 0;

  void _confirmar() {
    if (!_pagoCompleto) return;

    final usd = _parse(_usdCtrl.text);
    final bs = _parse(_bsCtrl.text);
    final pm = _parse(_pmCtrl.text);
    final tarjeta = _parse(_tarjetaCtrl.text);
    final fiado = _parse(_fiadoCtrl.text);

    final usdEnBs = usd * widget.tasa;
    final totalAbonado = usdEnBs + bs + pm + tarjeta + fiado;
    final vueltoBs = (totalAbonado - widget.totalBs).clamp(0, double.infinity).toDouble();
    final vueltoUsd = vueltoBs > 0 && widget.tasa > 0 ? (vueltoBs / widget.tasa) : 0.0;

    final detalle = PagoMixtoDetalle(
      divisasUsd: usd,
      divisasBs: usdEnBs,
      efectivoBs: bs,
      pagoMovilBs: pm,
      tarjetaBs: tarjeta,
      fiadoBs: fiado,
      totalAbonadoBs: totalAbonado,
      vueltoBs: vueltoBs,
      vueltoUsd: vueltoUsd,
    );

    widget.onConfirm?.call(detalle);
    Navigator.of(context).pop();
  }

  Widget _campo(String label, TextEditingController ctrl, IconData icon, {Color? iconColor}) {
    return TextField(
      controller: ctrl,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: iconColor ?? const Color(0xFF2563EB)),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
      ),
      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final esOscuro = Theme.of(context).brightness == Brightness.dark;
    final colorFondo = esOscuro ? const Color(0xFF1E293B) : Colors.white;
    final colorCard = esOscuro ? const Color(0xFF334155) : const Color(0xFFF8FAFC);
    final colorBorde = esOscuro ? const Color(0xFF475569) : const Color(0xFFE2E8F0);
    final colorTexto = esOscuro ? Colors.white : const Color(0xFF0F172A);
    final colorTextoSec = esOscuro ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

    return Dialog(
      insetPadding: const EdgeInsets.all(16),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 520, maxHeight: 620),
        decoration: BoxDecoration(
          color: colorFondo,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF2563EB),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.account_balance_wallet_rounded, color: Colors.white, size: 28),
                  const SizedBox(width: 12),
                  const Text(
                    '🔀 PAGO MIXTO / FRACCIONADO',
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ],
              ),
            ),

            // Total banner
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFEFF6FF),
                border: Border.all(color: const Color(0xFFBFDBFE), width: 1.5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'TOTAL A PAGAR:',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Color(0xFF1E3A8A)),
                  ),
                  Text(
                    'Bs ${widget.totalBs.toStringAsFixed(2)}  (\$${widget.totalUsd.toStringAsFixed(2)})',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Color(0xFF1E3A8A)),
                  ),
                ],
              ),
            ),

            // Formulario
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: colorCard,
                    border: Border.all(color: colorBorde),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      _campo('💵 Divisas (\$ USD)', _usdCtrl, Icons.attach_money, iconColor: const Color(0xFF16A34A)),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '= Bs ${_usdEnBs.toStringAsFixed(2)}',
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Color(0xFF2563EB)),
                              textAlign: TextAlign.end,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _campo('💵 Efectivo (Bs)', _bsCtrl, Icons.money_rounded),
                      const SizedBox(height: 12),
                      _campo('📲 Pago Móvil (Bs)', _pmCtrl, Icons.phone_android_rounded),
                      const SizedBox(height: 12),
                      _campo('💳 Tarjeta / Punto (Bs)', _tarjetaCtrl, Icons.credit_card_rounded),
                      const SizedBox(height: 12),
                      _campo('🤝 Fiado / Crédito (Bs)', _fiadoCtrl, Icons.handshake_rounded),
                    ],
                  ),
                ),
              ),
            ),

            // Status card
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _pagoCompleto
                    ? (esOscuro ? const Color(0xFF14532D) : const Color(0xFFF0FDF4))
                    : (esOscuro ? const Color(0xFF7F1D1D) : const Color(0xFFFEF2F2)),
                border: Border.all(
                  color: _pagoCompleto
                      ? (esOscuro ? const Color(0xFF86EFAC) : const Color(0xFF86EFAC))
                      : (esOscuro ? const Color(0xFFFCA5A5) : const Color(0xFFFCA5A5)),
                  width: 1.5,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Total Abonado:', style: TextStyle(fontSize: 14, color: colorTextoSec)),
                      Text(
                        'Bs ${_totalAbonado.toStringAsFixed(2)}',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: colorTexto),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _pagoCompleto ? (_diferencia > 0 ? '🎉 Vuelto a Entregar:' : '✅ PAGO EXACTO') : 'Resta por Pagar:',
                        style: TextStyle(fontSize: 14, color: colorTextoSec),
                      ),
                      Text(
                        _pagoCompleto
                            ? (_diferencia > 0
                                ? 'Bs ${_diferencia.toStringAsFixed(2)}  (\$${(_diferencia / widget.tasa).toStringAsFixed(2)})'
                                : '¡COMPLETO!')
                            : 'Bs ${(-_diferencia).toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w900,
                          color: _pagoCompleto ? const Color(0xFF16A34A) : const Color(0xFFDC2626),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Botones
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: BorderSide(color: colorBorde),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        foregroundColor: colorTexto,
                      ),
                      child: const Text('Cancelar', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: _pagoCompleto ? _confirmar : null,
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF16A34A),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        disabledBackgroundColor: const Color(0xFF94A3B8),
                      ),
                      child: const Text('✅ Confirmar Pago Mixto', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}