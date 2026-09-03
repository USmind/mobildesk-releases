import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import 'net_stub.dart';

const String kSupabaseUrl = 'https://atxeuhqhariymdqsbmpd.supabase.co';
const String kSupabaseKey = 'sb_publishable_6a_o_Jv_XhqZE9TP7mO2EA_gOeak-mL';

String toValidUuid(String text) {
  final trimmed = text.trim().toLowerCase();
  final regex = RegExp(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$');
  if (regex.hasMatch(trimmed)) {
    return trimmed;
  }
  final digest = md5.convert(utf8.encode(trimmed)).toString();
  return '${digest.substring(0, 8)}-${digest.substring(8, 12)}-${digest.substring(12, 16)}-${digest.substring(16, 20)}-${digest.substring(20, 32)}';
}

class AppState extends ChangeNotifier {
  String? token;
  String? refreshToken;
  String? businessId;
  String? email;

  String businessName = 'MobilDesk';
  double exchangeRate = 763.0;
  double profitMargin = 0.0;

  Map<String, Product> products = {};
  List<InventoryMovement> movements = [];
  List<Sale> sales = [];
  List<Map<String, dynamic>> outbox = [];
  Set<String> seenEvents = {};

  bool isSyncing = false;
  String syncStatus = 'Iniciando...';
  String? lastSyncTime;
  String? lastErrorMessage;

  // ---- Licencia sincronizada con el PC ----
  // estados: desconocida | demo | activo | vitalicio | expirado
  String licEstado = 'desconocida';
  String licPlan = '';
  String licFechaExpiracion = '';
  DateTime? firstInstall;

  Timer? _autoSyncTimer;

  bool get isAuthenticated => (businessId != null && businessId!.trim().isNotEmpty);

  DateTime? get _licExpiracion => DateTime.tryParse(licFechaExpiracion);

  /// La app se bloquea en el MISMO momento que el PC:
  /// ambos cuentan desde la misma fecha_expiracion.
  bool get licenciaBloqueada {
    if (licEstado == 'vitalicio') return false;
    if (licEstado == 'expirado') return true;
    if (licEstado == 'activo' || licEstado == 'demo') {
      final exp = _licExpiracion;
      if (exp == null) return false;
      return DateTime.now().isAfter(exp);
    }
    // Sin informacion del PC: prueba local de 7 dias desde la instalacion.
    final fi = firstInstall;
    if (fi == null) return false;
    return DateTime.now().isAfter(fi.add(const Duration(days: 7)));
  }

  /// Texto de tiempo restante (mismos dias y horas que el PC).
  String get licenciaRestanteTexto {
    if (licEstado == 'vitalicio') return 'Licencia permanente';
    DateTime? exp;
    if (licEstado == 'activo' || licEstado == 'demo') exp = _licExpiracion;
    exp ??= firstInstall?.add(const Duration(days: 7));
    if (exp == null) return '';
    final dif = exp.difference(DateTime.now());
    if (dif.isNegative) return 'Expirada';
    final d = dif.inDays;
    final h = dif.inHours.remainder(24);
    final m = dif.inMinutes.remainder(60);
    if (d > 0) return '$d días y $h horas';
    if (h > 0) return '$h horas y $m minutos';
    return '$m minutos';
  }

  String get licenciaEstadoTexto {
    switch (licEstado) {
      case 'vitalicio':
        return 'Permanente (Vitalicia)';
      case 'activo':
        return 'Activa';
      case 'demo':
        return 'Prueba Gratuita';
      case 'expirado':
        return 'Expirada';
      default:
        return 'Prueba (sin vincular al PC)';
    }
  }

  AppState() {
    load();
  }

  @override
  void dispose() {
    _autoSyncTimer?.cancel();
    super.dispose();
  }

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    token = prefs.getString('token');
    refreshToken = prefs.getString('refreshToken');
    businessId = prefs.getString('businessId');
    email = prefs.getString('email');
    businessName = prefs.getString('businessName') ?? 'MobilDesk POS';
    exchangeRate = prefs.getDouble('exchangeRate') ?? 763.0;
    profitMargin = prefs.getDouble('profitMargin') ?? 0.0;
    lastSyncTime = prefs.getString('lastSyncTime');

    final rawState = prefs.getString('kiosko_state_v6');
    if (rawState != null) {
      try {
        final data = jsonDecode(rawState) as Map<String, dynamic>;
        if (data['products'] is Map) {
          products = (data['products'] as Map).map(
            (k, v) => MapEntry(k.toString(), Product.fromMap(Map<String, dynamic>.from(v))),
          );
        }
        if (data['movements'] is List) {
          movements = (data['movements'] as List)
              .map((e) => InventoryMovement.fromMap(Map<String, dynamic>.from(e)))
              .toList();
        }
        if (data['sales'] is List) {
          sales = (data['sales'] as List)
              .map((e) => Sale.fromMap(Map<String, dynamic>.from(e)))
              .toList();
        }
        if (data['outbox'] is List) {
          outbox = List<Map<String, dynamic>>.from(data['outbox']);
        }
        if (data['seen'] is List) {
          seenEvents = Set<String>.from(data['seen']);
        }
        if (data['licEstado'] is String) licEstado = data['licEstado'];
        if (data['licPlan'] is String) licPlan = data['licPlan'];
        if (data['licFechaExpiracion'] is String) licFechaExpiracion = data['licFechaExpiracion'];
      } catch (e) {
        debugPrint('Error loading state: $e');
      }
    }

    final fiStr = prefs.getString('firstInstall');
    firstInstall = fiStr != null ? DateTime.tryParse(fiStr) : null;
    if (firstInstall == null) {
      firstInstall = DateTime.now();
      prefs.setString('firstInstall', firstInstall!.toIso8601String());
    }

    _autoSyncTimer?.cancel();
    _autoSyncTimer = Timer.periodic(const Duration(seconds: 8), (_) {
      if (isAuthenticated && !isSyncing) {
        sync();
      }
    });

    notifyListeners();
    if (isAuthenticated) {
      sync();
    } else {
      syncStatus = 'Ingresa el Código de tu Negocio';
      notifyListeners();
    }
  }

  Future<void> save() async {
    final prefs = await SharedPreferences.getInstance();
    if (token != null) await prefs.setString('token', token!);
    if (refreshToken != null) await prefs.setString('refreshToken', refreshToken!);
    if (businessId != null) await prefs.setString('businessId', businessId!);
    if (email != null) await prefs.setString('email', email!);
    if (lastSyncTime != null) await prefs.setString('lastSyncTime', lastSyncTime!);
    await prefs.setString('businessName', businessName);
    await prefs.setDouble('exchangeRate', exchangeRate);
    await prefs.setDouble('profitMargin', profitMargin);

    final rawData = {
      'products': products.map((k, v) => MapEntry(k, v.toMap())),
      'movements': movements.map((m) => m.toMap()).toList(),
      'sales': sales.map((s) => s.toMap()).toList(),
      'outbox': outbox,
      'seen': seenEvents.toList(),
      'licEstado': licEstado,
      'licPlan': licPlan,
      'licFechaExpiracion': licFechaExpiracion,
    };
    await prefs.setString('kiosko_state_v6', jsonEncode(rawData));
  }

  double calculateStock(String codigo) {
    double total = 0;
    for (final m in movements.where((m) => m.productoCodigo == codigo)) {
      if (m.tipo == 'salida') {
        total -= m.cantidad;
      } else {
        total += m.cantidad;
      }
    }
    return total;
  }

  double calculateSalePriceUsd(double basePriceUsd) {
    return basePriceUsd * (1 + profitMargin / 100);
  }

  double calculateSalePriceBs(double basePriceUsd) {
    return calculateSalePriceUsd(basePriceUsd) * exchangeRate;
  }

  void setExchangeRate(double newRate, [double? newMargin]) {
    if (newRate <= 0) return;
    exchangeRate = newRate;
    if (newMargin != null && newMargin >= 0) {
      profitMargin = newMargin;
    }
    queueEvent('tasa_cambio_actualizada', {
      'tasa': exchangeRate,
      'margen': profitMargin,
    });
    save();
    notifyListeners();
    sync();
  }

  void updateSettings({String? name, double? rate, double? margin, String? customBusinessId}) {
    if (name != null && name.trim().isNotEmpty) {
      businessName = name.trim();
      queueEvent('negocio_config_actualizada', {
        'nombre_negocio': businessName,
      });
    }
    if (rate != null && rate > 0) {
      exchangeRate = rate;
    }
    if (margin != null && margin >= 0) {
      profitMargin = margin;
    }
    if (rate != null || margin != null) {
      queueEvent('tasa_cambio_actualizada', {
        'tasa': exchangeRate,
        'margen': profitMargin,
      });
    }
    if (customBusinessId != null && customBusinessId.trim().isNotEmpty) {
      businessId = customBusinessId.trim().toUpperCase();
    }

    save();
    notifyListeners();
    sync();
  }

  void recordDebtPayment(String saleId, double amountPaid) {
    final idx = sales.indexWhere((s) => s.id == saleId);
    if (idx >= 0) {
      final old = sales[idx];
      final newBalance = (old.saldoPendiente - amountPaid).clamp(0.0, double.infinity);
      sales[idx] = Sale(
        id: old.id,
        numeroFactura: old.numeroFactura,
        tasa: old.tasa,
        totalUsd: old.totalUsd,
        totalBs: old.totalBs,
        metodoPago: old.metodoPago,
        montoRecibidoBs: old.montoRecibidoBs,
        montoRecibidoUsd: old.montoRecibidoUsd,
        vueltoBs: old.vueltoBs,
        vueltoUsd: old.vueltoUsd,
        clienteNombre: old.clienteNombre,
        esFiada: newBalance > 0,
        saldoPendiente: newBalance,
        fecha: old.fecha,
        productos: old.productos,
      );

      queueEvent('abono_deuda', {
        'numero_factura': old.numeroFactura,
        'cliente_nombre': old.clienteNombre,
        'monto_bs': amountPaid,
        'saldo_restante_bs': newBalance,
      });

      save();
      notifyListeners();
    }
  }

  void queueEvent(String tipo, Map<String, dynamic> datos) {
    final eventId = toValidUuid('mov-${DateTime.now().microsecondsSinceEpoch}-${Random().nextInt(99999)}');
    final payload = {
      'id': eventId,
      'tipo': tipo,
      'datos': datos,
      'creado_en': DateTime.now().toUtc().toIso8601String(),
    };
    outbox.add(payload);
    seenEvents.add(eventId);
    applyLocalEvent(tipo, datos, eventId);
    save();
    notifyListeners();
    sync();
  }

  void applyLocalEvent(String tipo, Map<String, dynamic> datos, [String? id]) {
    if (tipo == 'tasa_cambio_actualizada') {
      final rate = double.tryParse(datos['tasa']?.toString() ?? '');
      final margin = double.tryParse(datos['margen']?.toString() ?? '');
      if (rate != null && rate > 0) exchangeRate = rate;
      if (margin != null && margin >= 0) profitMargin = margin;
    } else if (tipo == 'negocio_config_actualizada') {
      final name = datos['nombre_negocio']?.toString();
      if (name != null && name.trim().isNotEmpty) {
        businessName = name.trim();
      }
    } else if (tipo == 'producto_guardado') {
      final p = Product.fromMap(datos);
      if (p.codigo.isNotEmpty) {
        products[p.codigo] = p;
      }
    } else if (tipo == 'producto_eliminado') {
      final code = datos['codigo']?.toString();
      if (code != null) {
        products.remove(code);
        movements.removeWhere((m) => m.productoCodigo == code);
      }
    } else if (tipo == 'movimiento_inventario') {
      final mov = InventoryMovement.fromMap(datos);
      final movId = (id != null && id.isNotEmpty) ? id : (datos['id']?.toString() ?? mov.id);
      final isDuplicate = movements.any((m) =>
          (movId.isNotEmpty && m.id == movId) ||
          (m.productoCodigo == mov.productoCodigo &&
              m.tipo == mov.tipo &&
              m.cantidad == mov.cantidad &&
              m.fecha == mov.fecha));
      if (!isDuplicate) {
        movements.add(InventoryMovement(
          id: movId,
          productoCodigo: mov.productoCodigo,
          tipo: mov.tipo,
          cantidad: mov.cantidad,
          costoUsd: mov.costoUsd,
          motivo: mov.motivo,
          fecha: mov.fecha,
        ));
      }
    } else if (tipo == 'venta_registrada') {
      final sale = Sale.fromMap(datos);
      final exists = sales.any((s) => s.numeroFactura == sale.numeroFactura && sale.numeroFactura.isNotEmpty);
      if (!exists) {
        sales.add(sale);
      }
    } else if (tipo == 'licencia_negocio') {
      final nuevoEstado = datos['estado']?.toString() ?? '';
      final nuevaFecha = datos['fecha_expiracion']?.toString() ?? '';
      if (nuevoEstado.isNotEmpty) licEstado = nuevoEstado;
      licPlan = datos['plan']?.toString() ?? '';
      licFechaExpiracion = nuevaFecha;
    } else if (tipo == 'abono_deuda') {
      final fac = datos['numero_factura']?.toString() ?? '';
      final monto = double.tryParse(datos['monto_bs']?.toString() ?? '0') ?? 0.0;
      final idx = sales.indexWhere((s) => s.numeroFactura == fac && fac.isNotEmpty);
      if (idx >= 0) {
        final old = sales[idx];
        final newBalance = (old.saldoPendiente - monto).clamp(0.0, double.infinity);
        sales[idx] = Sale(
          id: old.id,
          numeroFactura: old.numeroFactura,
          tasa: old.tasa,
          totalUsd: old.totalUsd,
          totalBs: old.totalBs,
          metodoPago: old.metodoPago,
          montoRecibidoBs: old.montoRecibidoBs,
          montoRecibidoUsd: old.montoRecibidoUsd,
          vueltoBs: old.vueltoBs,
          vueltoUsd: old.vueltoUsd,
          clienteNombre: old.clienteNombre,
          esFiada: newBalance > 0,
          saldoPendiente: newBalance,
          fecha: old.fecha,
          productos: old.productos,
        );
      }
    }
  }

  Future<void> connectWithBusinessCode(String code) async {
    code = code.trim().toLowerCase();
    if (code.isEmpty) {
      throw 'Escribe el código de tu negocio (ej: el que aparece en tu PC).';
    }

    businessId = code;
    email = 'código: $code';
    token = null;
    refreshToken = null;

    products.clear();
    movements.clear();
    sales.clear();
    seenEvents.clear();
    lastErrorMessage = null;

    await save();
    notifyListeners();
    await sync();
  }

  Future<void> login(String inputEmail, String password) async {
    inputEmail = inputEmail.trim().toLowerCase();
    if (!inputEmail.contains('@') || password.length < 8) {
      throw 'Escribe un correo válido y una contraseña de al menos 8 caracteres.';
    }

    Map<String, dynamic> sessionData;

    try {
      sessionData = await _rawApi(
        '/auth/v1/token?grant_type=password',
        'POST',
        {'email': inputEmail, 'password': password},
        null,
      );
    } catch (loginErr) {
      final newBusinessId = 'negocio-${Random().nextInt(999999)}';
      try {
        final signupRes = await _rawApi(
          '/auth/v1/signup',
          'POST',
          {
            'email': inputEmail,
            'password': password,
            'data': {'negocio_id': newBusinessId},
          },
          null,
        );
        if (signupRes['session'] != null) {
          sessionData = signupRes['session'];
        } else {
          sessionData = await _rawApi(
            '/auth/v1/token?grant_type=password',
            'POST',
            {'email': inputEmail, 'password': password},
            null,
          );
        }
      } catch (signupErr) {
        throw 'Error al autenticar con correo ($loginErr). Tip: Puedes usar la opción de "Enlazar con Código de Negocio" que es instantánea.';
      }
    }

    token = sessionData['access_token']?.toString();
    refreshToken = sessionData['refresh_token']?.toString();
    email = inputEmail;

    try {
      final userData = await _rawApi('/auth/v1/user', 'GET', null, token);
      final metadata = userData['user_metadata'] as Map<String, dynamic>?;
      businessId = metadata?['negocio_id']?.toString();
    } catch (_) {}

    if (businessId == null || businessId!.isEmpty) {
      final user = sessionData['user'] as Map<String, dynamic>?;
      final metadata = user?['user_metadata'] as Map<String, dynamic>?;
      businessId = metadata?['negocio_id']?.toString() ?? 'kiosko-default';
    }

    products.clear();
    movements.clear();
    sales.clear();
    seenEvents.clear();
    lastErrorMessage = null;

    await save();
    notifyListeners();
    await sync();
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('refreshToken');
    await prefs.remove('businessId');
    await prefs.remove('kiosko_state_v6');
    token = null;
    refreshToken = null;
    businessId = null;
    products.clear();
    movements.clear();
    sales.clear();
    seenEvents.clear();
    syncStatus = 'Sesión cerrada';
    lastErrorMessage = null;
    notifyListeners();
  }

  Future<void> sync() async {
    if (isSyncing) return;
    if (!isAuthenticated) {
      syncStatus = 'Ingresa el Código de Negocio';
      notifyListeners();
      return;
    }

    final validUuid = toValidUuid(businessId!);

    isSyncing = true;
    syncStatus = 'Sincronizando con la nube...';
    notifyListeners();

    try {
      // 1. Enviar eventos locales pendientes (outbox)
      // Un duplicado (23505) significa que el evento ya está en la nube:
      // se descarta localmente en vez de abortar toda la sincronización.
      final outboxCopy = List<Map<String, dynamic>>.from(outbox);
      for (final event in outboxCopy) {
        try {
          await _authenticatedApi(
            '/rest/v1/kiosko_sync_events',
            'POST',
            {
              'id': toValidUuid(event['id']),
              'negocio_id': validUuid,
              'dispositivo_id': toValidUuid('movil-$validUuid'),
              'tipo': event['tipo'],
              'datos': event['datos'],
              'creado_en': event['creado_en'],
            },
          );
        } catch (e) {
          if (!_isDuplicateKeyError(e.toString())) rethrow;
        }
        outbox.removeWhere((e) => e['id'] == event['id']);
      }

      // 2. Descargar todos los eventos del negocio
      final remoteEvents = await _authenticatedApi(
        '/rest/v1/kiosko_sync_events?select=id,tipo,datos,creado_en&negocio_id=eq.$validUuid&order=creado_en.asc',
        'GET',
      );

      if (remoteEvents is List) {
        for (final item in remoteEvents) {
          final eventMap = Map<String, dynamic>.from(item);
          final eventId = eventMap['id']?.toString() ?? '';
          if (seenEvents.add(eventId)) {
            final tipo = eventMap['tipo']?.toString() ?? '';
            final datos = Map<String, dynamic>.from(eventMap['datos'] ?? {});
            applyLocalEvent(tipo, datos, eventId);
          }
        }
      }

      final now = DateTime.now();
      final timeFormatted = '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
      lastSyncTime = timeFormatted;
      syncStatus = 'Sincronizado ($timeFormatted) · ${products.length} productos';
      lastErrorMessage = null;
      await save();
    } catch (e) {
      final friendlyError = _translateError(e.toString());
      lastErrorMessage = friendlyError;
      syncStatus = friendlyError;
      debugPrint('Sync error: $e');
    } finally {
      isSyncing = false;
      notifyListeners();
    }
  }

  bool _isDuplicateKeyError(String raw) {
    final lower = raw.toLowerCase();
    return lower.contains('duplicate key') ||
        lower.contains('23505') ||
        lower.contains('kiosko_sync_events_pkey') ||
        lower.contains('already exists');
  }

  String _translateError(String raw) {    final lower = raw.toLowerCase();
    if (lower.contains('permission denied') || lower.contains('42501') || lower.contains('401')) {
      return 'Faltan permisos en Supabase. Ejecuta el script SQL en tu panel de Supabase.';
    }
    if (lower.contains('invalid input syntax for type uuid') || lower.contains('22p02')) {
      return 'Formato de código actualizado. Sincronizando...';
    }
    if (lower.contains('socketexception') || lower.contains('failed host lookup') || lower.contains('network is unreachable')) {
      return 'Sin conexión a Internet';
    }
    if (lower.contains('timeout')) {
      return 'Tiempo de espera agotado al conectar con la nube';
    }
    if (lower.contains('429') || lower.contains('rate limit')) {
      return 'Demasiados intentos seguidos. Usa el Código de Negocio.';
    }
    if (lower.contains('invalid login') || lower.contains('invalid credentials')) {
      return 'El correo o la contraseña no son correctos.';
    }
    if (lower.contains('permission denied') || lower.contains('camera permission')) {
      return 'Permiso de cámara denegado. Ve a Ajustes > Aplicaciones > MobilDesk POS > Permisos > Cámara y actívalo.';
    }
    if (lower.contains('camera') && lower.contains('not available')) {
      return 'La cámara no está disponible en este dispositivo.';
    }
    if (lower.contains('unexpected error') || lower.contains('unexpected error occurred')) {
      return 'Ocurrió un error inesperado. Intenta de nuevo.';
    }
    if (lower.contains('null') || lower.contains('null object reference')) {
      return 'Error interno. Reinicia la aplicación e inténtalo de nuevo.';
    }
    return 'Aviso: $raw';
  }

  Future<dynamic> _authenticatedApi(String path, String method, [Object? data]) async {
    try {
      return await _rawApi(path, method, data, token);
    } catch (e) {
      if (token != null) {
        try {
          return await _rawApi(path, method, data, null);
        } catch (_) {}
      }
      rethrow;
    }
  }

  static Future<dynamic> _rawApi(String path, String method, [Object? data, String? authToken]) async {
    final headers = <String, String>{
      'apikey': kSupabaseKey,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (authToken != null && authToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $authToken';
    }
    final body = data != null ? jsonEncode(data) : null;
    final text = await fetchRaw(
      kSupabaseUrl + path,
      method: method,
      headers: headers,
      body: body,
    );
    return text.isEmpty ? {} : jsonDecode(text);
  }

  Future<Map<String, dynamic>?> checkAppUpdate() async {
    try {
      final text = await fetchRaw(
        'https://raw.githubusercontent.com/USmind/mobildesk-releases/main/version.json',
        timeout: const Duration(seconds: 10),
      );
      return jsonDecode(text) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Error al verificar actualización: $e');
      return null;
    }
  }
}
