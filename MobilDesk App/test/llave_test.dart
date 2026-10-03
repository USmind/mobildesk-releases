import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';

/// Copia exacta de la funcion en lib/services/app_state.dart
const String kLlaveSemilla = 'mobildesk-sync-v1';

String derivarLlave(String codigoNegocio) {
  final base = codigoNegocio.trim().toLowerCase();
  if (base.isEmpty) return '';
  final hmacSha256 = Hmac(sha256, utf8.encode(kLlaveSemilla));
  return hmacSha256.convert(utf8.encode(base)).toString();
}

void main() {
  test('La llave del movil coincide con la del PC', () {
    // Valor calculado por el PC (Python, mismo algoritmo HMAC-SHA256)
    expect(derivarLlave('MOBIL-6541'),
        'ca375b122d7c05d87eff1a0639ec95446861135c8493c5911e520e7cc34bded9');
  });

  test('Mayusculas, minusculas y espacios dan la misma llave', () {
    final a = derivarLlave('MOBIL-6541');
    expect(derivarLlave('mobil-6541'), a);
    expect(derivarLlave('  MOBIL-6541  '), a);
  });

  test('Codigos distintos dan llaves distintas', () {
    expect(derivarLlave('MOBIL-6541'), isNot(derivarLlave('OTRA-9999')));
  });

  test('Codigo vacio devuelve cadena vacia', () {
    expect(derivarLlave(''), '');
    expect(derivarLlave('   '), '');
  });

  test('La llave tiene 64 caracteres hexadecimales', () {
    final k = derivarLlave('MOBIL-6541');
    expect(k.length, 64);
    expect(RegExp(r'^[0-9a-f]{64}$').hasMatch(k), isTrue,
        reason: 'debe ser hex minuscula de 64 caracteres');
  });

  test('toValidUuid coincide con el MD5 del PC', () {
    // PC: md5('mobil-6541') -> UUID
    expect(toValidUuidLocal('MOBIL-6541'),
        'b8cc3682-1410-d48c-e5c6-eabf7b18645b');
  });
}

String toValidUuidLocal(String text) {
  final trimmed = text.trim().toLowerCase();
  final regex = RegExp(
      r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$');
  if (regex.hasMatch(trimmed)) return trimmed;
  final d = md5.convert(utf8.encode(trimmed)).toString();
  return '${d.substring(0, 8)}-${d.substring(8, 12)}-${d.substring(12, 16)}-'
      '${d.substring(16, 20)}-${d.substring(20, 32)}';
}