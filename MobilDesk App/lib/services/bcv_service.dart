/// Servicio para obtener la tasa oficial del BCV automáticamente.
///
/// Fuente: https://bcv.today/api/v1/rate.json (gratis, sin API key)
/// La API retorna JSON con las tasas de todas las monedas: USD, EUR, CNY, TRY, RUB.

import 'dart:convert';
import 'net_stub.dart';

const _bcvApiUrl = 'https://bcv.today/api/v1/rate.json';

/// Resultado del fetch de tasa BCV.
class BcvRateResult {
  final double rate;
  final String date;
  final String updatedAt;

  const BcvRateResult({required this.rate, required this.date, required this.updatedAt});
}

/// Obtiene la tasa oficial USD/Bs del BCV.
/// Retorna null si falla.
Future<BcvRateResult?> fetchBcvRate() async {
  try {
    final text = await fetchRaw(
      _bcvApiUrl,
      headers: {'Cache-Control': 'no-cache'},
    );
    final data = jsonDecode(text) as Map<String, dynamic>;
    final usdRate = data['USD'];
    if (usdRate == null) return null;
    final rate = double.tryParse(usdRate.toString());
    if (rate == null || rate <= 0) return null;
    return BcvRateResult(
      rate: rate,
      date: (data['date'] ?? '').toString(),
      updatedAt: (data['updated_at'] ?? '').toString(),
    );
  } catch (_) {
    return null;
  }
}
