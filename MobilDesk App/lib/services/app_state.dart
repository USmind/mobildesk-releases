import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:open_filex/open_filex.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/models.dart';
import 'net_stub.dart';
import 'bcv_service.dart';
import '../config.dart';

/// Clave donde se guarda el estado local del móvil (datos + cola de eventos).
/// Antes estaba escrita como texto literal 'kiosko_state_v6' en varios puntos,
/// lo que hacía fácil olvidarla al limpiarla.
const String kPrefState = 'kiosko_state_v6';

String toValidUuid(String text) {
  final trimmed = text.trim().toLowerCase();
  final regex = RegExp(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$');
  if (regex.hasMatch(trimmed)) {
    return trimmed;
  }
  final digest = md5.convert(utf8.encode(trimmed)).toString();
  return '${digest.substring(0, 8)}-${digest.substring(8, 12)}-${digest.substring(12, 16)}-${digest.substring(16, 20)}-${digest.substring(20, 32)}';
}

/// Semilla para derivar la llave del negocio. Debe ser IDENTICA a la del PC
/// (modules/sync/sync_service.py), porque ambos calculan la llave a partir del
/// mismo codigo de negocio sin tener que descargarla de la nube.
const String kLlaveSemilla = 'mobildesk-sync-v1';

/// Calcula la llave del negocio a partir de su codigo.
///
/// Es determinista: el mismo codigo produce siempre la misma llave, de modo que
/// el movil y la computadora generan la misma. Postgres la valida para que cada
/// negocio solo vea lo suyo.
String derivarLlave(String codigoNegocio) {
  final base = codigoNegocio.trim().toLowerCase();
  if (base.isEmpty) return '';
  final hmacSha256 = Hmac(sha256, utf8.encode(kLlaveSemilla));
  return hmacSha256.convert(utf8.encode(base)).toString();
}

class AppState extends ChangeNotifier {
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

  // ---- Licencia sincronizada con el PC ----
  // estados: desconocida | demo | activo | vitalicio | expirado
  String licEstado = 'desconocida';
  String licFechaExpiracion = '';
  DateTime? firstInstall;

  Timer? _autoSyncTimer;
  Timer? _bcvAutoTimer;
  String? lastBcvUpdate;

  /// Cliente elegido desde Cobrar/Fiados para fiarle más.
  /// La pantalla Vender lo consume al abrirse (pone el nombre y método fiado).
  /// Es transitorio: no se persiste ni se sincroniza.
  String? clienteParaFiar;

  bool get isAuthenticated => (businessId != null && businessId!.trim().isNotEmpty);

  DateTime? get _licExpiracion => DateTime.tryParse(licFechaExpiracion);

  /// La app se bloquea en el MISMO momento que el PC:
  /// ambos cuentan desde la misma fecha_expiracion.
  bool get licenciaBloqueada {
    if (licEstado == 'vitalicio') return false;
    if (licEstado == 'expirado') return true;
    if (licEstado == 'activo' || licEstado == 'demo') {
      final exp = _licExpiracion;
      // Si dice activa pero no hay fecha, el PC aún no la sincronizó.
      // Antes devolvía false y dejaba la app desbloqueada indefinidamente.
      // Ahora cae a la prueba local de 7 días.
      if (exp == null) {
        final fi0 = firstInstall;
        if (fi0 == null) return true;
        return DateTime.now().isAfter(fi0.add(const Duration(days: 7)));
      }
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

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    businessId = prefs.getString('businessId');
    email = prefs.getString('email');
    businessName = prefs.getString('businessName') ?? 'MobilDesk POS';
    exchangeRate = prefs.getDouble('exchangeRate') ?? 763.0;
    profitMargin = prefs.getDouble('profitMargin') ?? 0.0;

    final rawState = prefs.getString(kPrefState);
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
        if (data['licFechaExpiracion'] is String) licFechaExpiracion = data['licFechaExpiracion'];
      } catch (e) {
        debugPrint('Error loading state: $e');
      }
    }

    // Al arrancar, normalizar los saldos: datos viejos solo tienen el Bs congelado
    // con la tasa del momento de la venta, hay que derivar el USD y revalorar.
    _revalorarSaldos();

    final fiStr = prefs.getString('firstInstall');
    firstInstall = fiStr != null ? DateTime.tryParse(fiStr) : null;
    if (firstInstall == null) {
      firstInstall = DateTime.now();
      prefs.setString('firstInstall', firstInstall!.toIso8601String());
    }

    _autoSyncTimer?.cancel();
    // Sync cada 30-60 segundos con jitter para evitar picos de conexión simultáneos
    final baseInterval = 30 + Random().nextInt(30);
    _autoSyncTimer = Timer.periodic(Duration(seconds: baseInterval), (_) {
      if (isAuthenticated && !isSyncing) {
        sync();
      }
    });

    // Auto-fetch tasa BCV al inicio y cada hora
    fetchBcvRateAndUpdate();
    _bcvAutoTimer?.cancel();
    _bcvAutoTimer = Timer.periodic(const Duration(hours: 1), (_) {
      fetchBcvRateAndUpdate();
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
    if (businessId != null) await prefs.setString('businessId', businessId!);
    if (email != null) await prefs.setString('email', email!);
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
      'licFechaExpiracion': licFechaExpiracion,
    };
    await prefs.setString(kPrefState, jsonEncode(rawData));
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
    _revalorarSaldos();
    queueEvent('tasa_cambio_actualizada', {
      'tasa': exchangeRate,
      'margen': profitMargin,
    });
    save();
    notifyListeners();
    sync();
  }

  /// Recalcula el saldo en Bs de cada venta fiada usando la tasa vigente.
  /// El USD es la fuente de verdad; el Bs se deriva. Sin esto, cambiar la tasa
  /// dejaba el saldo del movil congelado y distinto al del PC.
  void _revalorarSaldos() {
    if (exchangeRate <= 0) return;
    for (var i = 0; i < sales.length; i++) {
      final s = sales[i];
      if (!s.esFiada) continue;
      final usd = s.saldoPendienteUsd > 0
          ? s.saldoPendienteUsd
          : (s.tasa > 0 ? s.saldoPendiente / s.tasa : 0.0);
      if (usd <= 0) continue;
      sales[i] = Sale(
        id: s.id,
        numeroFactura: s.numeroFactura,
        tasa: s.tasa,
        totalUsd: s.totalUsd,
        totalBs: s.totalBs,
        metodoPago: s.metodoPago,
        montoRecibidoBs: s.montoRecibidoBs,
        montoRecibidoUsd: s.montoRecibidoUsd,
        vueltoBs: s.vueltoBs,
        vueltoUsd: s.vueltoUsd,
        clienteNombre: s.clienteNombre,
        esFiada: usd > 0,
        saldoPendiente: usd * exchangeRate,
        saldoPendienteUsd: usd,
        fecha: s.fecha,
        productos: s.productos,
        pagosDetalle: s.pagosDetalle,
      );
    }
  }

  /// Obtiene la tasa BCV automáticamente y la aplica al sistema.
  /// No lanza excepciones: sin internet simplemente no hace nada.
  Future<void> fetchBcvRateAndUpdate() async {
    try {
      final result = await fetchBcvRate();
      if (result != null && result.rate > 0) {
        final oldRate = exchangeRate;
        exchangeRate = result.rate;
        lastBcvUpdate = result.date;
        if (oldRate != result.rate) {
          queueEvent('tasa_cambio_actualizada', {
            'tasa': exchangeRate,
            'margen': profitMargin,
          });
          save();
          notifyListeners();
        }
      }
    } catch (e) {
      debugPrint('BCV fetch sin conexión: $e');
    }
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

  void recordDebtPayment(String saleKey, double amountPaid, {String? metodo, double? montoUsd}) {
    // Buscar por numero_factura (unico y presente). Antes buscaba por id, que llega
    // vacio desde el PC y desde el movil, por lo que SIEMPRE terminaba en la primera
    // venta de la lista y los abonos se aplicaban a la factura equivocada.
    final idx = sales.indexWhere(
      (s) => (saleKey.isNotEmpty && s.numeroFactura == saleKey) ||
          (saleKey.isEmpty && s.id.isNotEmpty && s.id.isNotEmpty),
    );
    if (idx >= 0) {
      final old = sales[idx];
      // Descontar en USD (fuente de verdad) y derivar el Bs con la tasa vigente.
      final saldoUsdPrevio = old.saldoPendienteUsd > 0
          ? old.saldoPendienteUsd
          : (exchangeRate > 0 ? old.saldoPendiente / exchangeRate : 0.0);
      final abonoUsd = montoUsd ?? (exchangeRate > 0 ? amountPaid / exchangeRate : 0.0);
      var newBalanceUsd = (saldoUsdPrevio - abonoUsd);
      if (newBalanceUsd.abs() < 0.005) newBalanceUsd = 0.0;
      final newBalance = exchangeRate > 0 ? newBalanceUsd * exchangeRate : 0.0;
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
        esFiada: newBalanceUsd > 0,
        saldoPendiente: newBalance,
        saldoPendienteUsd: newBalanceUsd,
        fecha: old.fecha,
        productos: old.productos,
        pagosDetalle: old.pagosDetalle,
      );

      final datosAbono = <String, dynamic>{
        'numero_factura': old.numeroFactura,
        'cliente_nombre': old.clienteNombre,
        'monto_bs': amountPaid,
        'monto_usd': abonoUsd,
        'saldo_restante_bs': newBalance,
        'saldo_restante_usd': newBalanceUsd,
      };
      if (metodo != null && metodo.isNotEmpty) datosAbono['metodo'] = metodo;
      queueEvent('abono_deuda', datosAbono);

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

  Future<void> applyLocalEvent(String tipo, Map<String, dynamic> datos, [String? id]) async {
    if (tipo == 'tasa_cambio_actualizada') {
      final rate = double.tryParse(datos['tasa']?.toString() ?? '');
      final margin = double.tryParse(datos['margen']?.toString() ?? '');
      if (rate != null && rate > 0) exchangeRate = rate;
      if (margin != null && margin >= 0) profitMargin = margin;
      // Revalorar los saldos fiados con la tasa que acaba de llegar del PC,
      // para que el movil muestre lo mismo que la computadora.
      _revalorarSaldos();
    } else if (tipo == 'negocio_datos_borrados') {
      // El administrador borró todo desde la computadora: el móvil debe
      // quedarse igual de vacío, si no conserva datos de un negocio que ya no
      // existen y vuelve a subirlos en la siguiente sincronización.
      await _borrarTodoLocalmente();
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
    } else if (tipo == 'producto_recodificado') {
      final codigoAnterior = datos['codigo_anterior']?.toString() ?? '';
      final rawProd = datos['producto'];
      if (codigoAnterior.isNotEmpty && rawProd is Map) {
        final nuevo = Product.fromMap(Map<String, dynamic>.from(rawProd));
        if (nuevo.codigo.isNotEmpty) {
          products.remove(codigoAnterior);
          for (var i = 0; i < movements.length; i++) {
            final m = movements[i];
            if (m.productoCodigo == codigoAnterior) {
              movements[i] = InventoryMovement(
                id: m.id,
                productoCodigo: nuevo.codigo,
                tipo: m.tipo,
                cantidad: m.cantidad,
                costoUsd: m.costoUsd,
                motivo: m.motivo,
                fecha: m.fecha,
              );
            }
          }
          products[nuevo.codigo] = nuevo;
        }
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
      // Deduplicar solo por id estable (el snapshot del PC manda 'snap-<id>').
      // Antes se comparaban producto+tipo+cantidad+fecha, lo que fusionaba dos
      // movimientos LEGÍTIMOS que casualmente coincidían.
      final isDuplicate = movId.isNotEmpty && movements.any((m) => m.id == movId);
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
      licFechaExpiracion = nuevaFecha;
    } else if (tipo == 'abono_deuda') {
      final fac = datos['numero_factura']?.toString() ?? '';
      final idx = sales.indexWhere((s) => s.numeroFactura == fac && fac.isNotEmpty);
      if (idx >= 0) {
        final old = sales[idx];
        // El PC ya envio el saldo restante calculado; usarlo evita que el movil
        // recalcule con otra tasa y quede desincronizado.
        final usdNuevo = double.tryParse(datos['saldo_restante_usd']?.toString() ?? '');
        final saldoUsd = usdNuevo ??
            (exchangeRate > 0
                ? (old.saldoPendienteUsd > 0 ? old.saldoPendienteUsd : old.saldoPendiente / exchangeRate) -
                    (double.tryParse(datos['monto_usd']?.toString() ?? '') ?? 0.0)
                : 0.0);
        final saldoUsdFinal = saldoUsd.abs() < 0.005 ? 0.0 : saldoUsd;
        final newBalance = exchangeRate > 0 ? saldoUsdFinal * exchangeRate : 0.0;
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
          esFiada: saldoUsdFinal > 0,
          saldoPendiente: newBalance,
          saldoPendienteUsd: saldoUsdFinal,
          fecha: old.fecha,
          productos: old.productos,
          pagosDetalle: old.pagosDetalle,
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

    products.clear();
    movements.clear();
    sales.clear();
    outbox.clear();
    seenEvents.clear();

    await save();
    notifyListeners();
    await sync();
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('businessId');
    await prefs.remove(kPrefState);
    businessId = null;
    products.clear();
    movements.clear();
    sales.clear();
    outbox.clear();
    seenEvents.clear();
    syncStatus = 'Sesión cerrada';
    notifyListeners();
  }

  /// Vacía por completo los datos guardados en el móvil.
  ///
  /// Se llama al recibir el evento 'negocio_datos_borrados', que envía la
  /// computadora cuando el administrador borra todos los datos. Se elimina
  /// también el código de negocio y la sesión, para que la app vuelva al
  /// estado de instalación nueva: nada de lo que había antes debe quedar.
  Future<void> _borrarTodoLocalmente() async {
    products.clear();
    movements.clear();
    sales.clear();
    outbox.clear();
    seenEvents.clear();

    final prefs = await SharedPreferences.getInstance();
    // El estado guardado y la clave del código permitirían reconstruir datos
    // que ya no existen; se borran ambas cosas.
    await prefs.remove(kPrefState);
    await prefs.remove('businessId');
    await prefs.remove('email');
    await prefs.remove('businessName');

    businessId = null;
    email = null;
    businessName = 'MobilDesk POS';
    exchangeRate = 763.0;
    profitMargin = 0.0;
    syncStatus = 'Los datos del negocio fueron borrados desde la computadora';
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
            '/rest/v1/mobildesk_eventos',
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

      // 2. Descargar eventos del negocio CON PAGINACIÓN (100 por página)
      // Evita descargar todo el historial de una vez y timeouts.
      const pageSize = 100;
      int offset = 0;
      bool hasMore = true;

      while (hasMore) {
        final remoteEvents = await _authenticatedApi(
          '/rest/v1/mobildesk_eventos?select=id,tipo,datos,creado_en&negocio_id=eq.$validUuid&order=creado_en.asc&limit=$pageSize&offset=$offset',
          'GET',
        );

        if (remoteEvents is List && remoteEvents.isNotEmpty) {
          for (final item in remoteEvents) {
            final eventMap = Map<String, dynamic>.from(item);
            final eventId = eventMap['id']?.toString() ?? '';
            if (seenEvents.add(eventId)) {
              final tipo = eventMap['tipo']?.toString() ?? '';
              final datos = Map<String, dynamic>.from(eventMap['datos'] ?? {});
              await applyLocalEvent(tipo, datos, eventId);
            }
          }
          if (remoteEvents.length < pageSize) {
            hasMore = false;
          } else {
            offset += pageSize;
          }
        } else {
          hasMore = false;
        }
      }

      final now = DateTime.now();
      final timeFormatted = '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
      syncStatus = 'Sincronizado ($timeFormatted) · ${products.length} productos';
      await save();
    } catch (e) {
      final friendlyError = _translateError(e.toString());
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
        lower.contains('mobildesk_eventos_pkey') ||
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
    // La tabla en la nube todavia no existe. Es lo mas frecuente al actualizar
    // y hay que decirlo claro, porque el mensaje tecnico termina en 'null' y
    // el movil lo muestra como 'Error interno'.
    if (lower.contains('pgrst205') ||
        lower.contains('could not find the table') ||
        lower.contains('schema cache')) {
      return 'La nube todavia no tiene la tabla de sincronizacion.\n\n'
          'Ejecuta en Supabase el archivo\n'
          'sql/01_crear_mobildesk_eventos.sql\n'
          'y luego sql/02_registrar_llave.sql.\n\n'
          'Puedes vender con normalidad: todo queda guardado en este\n'
          'telefono y se subira al completarlo.';
    }
    if (lower.contains('permission denied') && !lower.contains('camera permission')) {
      return 'El servidor de sincronizacion esta actualizando permisos. Reintenta en unos segundos.';
    }
    if (lower.contains('camera permission')) {
      return 'Permiso de camara denegado. Ve a Ajustes > Aplicaciones > MobilDesk POS > Permisos > Camara y activalo.';
    }
    if (lower.contains('camera') && lower.contains('not available')) {
      return 'La camara no esta disponible en este dispositivo.';
    }
    if (lower.contains('unexpected error') || lower.contains('unexpected error occurred')) {
      return 'Ocurrio un error inesperado. Intenta de nuevo.';
    }
    if (lower.contains('null') || lower.contains('null object reference')) {
      return 'Error interno. Reinicia la aplicacion e intentalo de nuevo.';
    }
    return 'Aviso: $raw';
  }

  Future<dynamic> _authenticatedApi(String path, String method, [Object? data]) async {
    // La llave se deriva del codigo de negocio y la valida Postgres para aislar
    // los datos de cada cliente en la nube. Ya no hay sesion con token: el
    // login es por codigo de negocio.
    final llave = businessId == null ? '' : derivarLlave(businessId!);
    return _rawApi(path, method, data, null, llave);
  }

  static Future<dynamic> _rawApi(String path, String method, [Object? data, String? authToken, String? llave]) async {
    final headers = <String, String>{
      'apikey': kSupabaseKey,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (authToken != null && authToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $authToken';
    }
    // Cabecera que valida el candado en Postgres. Sin ella, la base rechaza
    // la peticion aunque la clave publica sea correcta.
    if (llave != null && llave.isNotEmpty) {
      headers['x-mobildesk-key'] = llave;
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
      final bust = kVersionJsonUrl.contains('?') ? '&t=${DateTime.now().millisecondsSinceEpoch}' : '?t=${DateTime.now().millisecondsSinceEpoch}';
      final text = await fetchRaw(
        '$kVersionJsonUrl$bust',
        timeout: const Duration(seconds: 10),
      );
      return jsonDecode(text) as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Error al verificar actualización: $e');
      rethrow;
    }
  }

  /// Compara dos strings de versión (ej: "v1.2.6" vs "1.2.7"). Retorna true si remote es más nueva.
  static bool _isNewerVersion(String remote, String current) {
    try {
      String clean(String v) => v.trim().toLowerCase().replaceAll(RegExp(r'^v'), '');
      final rParts = clean(remote).split('.').map((s) => int.tryParse(s) ?? 0).toList();
      final cParts = clean(current).split('.').map((s) => int.tryParse(s) ?? 0).toList();
      for (var i = 0; i < max(rParts.length, cParts.length); i++) {
        final r = i < rParts.length ? rParts[i] : 0;
        final c = i < cParts.length ? cParts[i] : 0;
        if (r > c) return true;
        if (r < c) return false;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Retorna la versión actual instalada de la app.
  Future<String> getCurrentVersion() async {
    final info = await PackageInfo.fromPlatform();
    return info.version;
  }

  /// Verifica si hay una actualización disponible. Retorna info de la update o null.
  Future<Map<String, dynamic>?> checkForUpdate() async {
    final remote = await checkAppUpdate();
    if (remote == null) return null;
    final remoteVersion = (remote['android_version'] ?? remote['version'] ?? '').toString().trim();
    if (remoteVersion.isEmpty) return null;
    final currentVersion = await getCurrentVersion();
    if (!_isNewerVersion(remoteVersion, currentVersion)) return null;
    return {
      'version': remoteVersion,
      'download_url': remote['android_download_url'] ?? remote['download_url'] ?? '',
      'changelog': remote['changelog'] ?? 'Mejoras de rendimiento y estabilidad.',
      'current_version': currentVersion,
    };
  }

  /// Descarga el APK a la caché de la app y retorna la ruta del archivo.
  Future<String?> downloadApk(String url, void Function(double percent, int downloaded, int total)? onProgress) async {
    try {
      final dir = await getTemporaryDirectory();
      final filePath = '${dir.path}/MobilDesk_Update.apk';
      final file = File(filePath);
      if (await file.exists()) await file.delete();

      final client = http.Client();
      final req = http.Request('GET', Uri.parse(url));
      req.headers['User-Agent'] = 'MobilDesk-App/${await getCurrentVersion()}';
      req.followRedirects = true;
      final streamed = await client.send(req).timeout(const Duration(seconds: 30));
      if (streamed.statusCode != 200) {
        debugPrint('HTTP ${streamed.statusCode} al descargar APK');
        client.close();
        return null;
      }
      final totalSize = streamed.contentLength ?? 0;
      var bytesDown = 0;
      final sink = file.openWrite();
      await for (final chunk in streamed.stream.timeout(const Duration(seconds: 60))) {
        sink.add(chunk);
        bytesDown += chunk.length;
        if (onProgress != null && totalSize > 0) {
          onProgress(bytesDown / totalSize, bytesDown, totalSize);
        }
      }
      await sink.flush();
      await sink.close();
      client.close();

      if (await file.exists() && await file.length() > 5000) {
        return filePath;
      }
      return null;
    } catch (e) {
      debugPrint('Error descargando APK: $e');
      return null;
    }
  }

  /// Abre el APK con el instalador del sistema Android.
  Future<bool> openApkForInstall(String filePath) async {
    try {
      final res = await OpenFilex.open(filePath, type: 'application/vnd.android.package-archive');
      debugPrint('OpenFilex result: ${res.type} ${res.message}');
      return res.type == ResultType.done;
    } catch (e) {
      debugPrint('Error abriendo APK: $e');
      // Fallback: intentar con url_launcher
      try {
        final uri = Uri.file(filePath);
        if (await canLaunchUrl(uri)) {
          return await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      } catch (_) {}
      return false;
    }
  }

  /// Fallback: abrir URL de descarga en navegador externo.
  Future<bool> openDownloadInBrowser(String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        return await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
      return false;
    } catch (e) {
      debugPrint('Error abriendo navegador: $e');
      return false;
    }
  }

  // NOTA: aqui habia fetchAppUsers(), que descargaba la lista de usuarios del
  // PC. Se elimino porque nada la leia: el login es por codigo de negocio y la
  // sesion por usuario quedo fuera. Los eventos 'usuario_sincronizado' que aun
  // lleguen se ignoran sin romper la sincronizacion.
}
