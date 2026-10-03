import 'package:flutter_test/flutter_test.dart';
import 'package:mobildesk_movil/services/app_state.dart';

/// Prueba las funciones REALES de sincronizacion (no copias locales).
/// Si alguien cambia derivarLlave/toValidUuid en app_state.dart y rompe la
/// compatibilidad con la PC, estos tests fallan.
void main() {
  test('La llave del movil coincide con la del PC', () {
    // Valor calculado por la PC (Python, mismo algoritmo HMAC-SHA256)
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
    expect(toValidUuid('MOBIL-6541'),
        'b8cc3682-1410-d48c-e5c6-eabf7b18645b');
  });
}
