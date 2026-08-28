class Product {
  final String codigo;
  final String codigoBarras;
  final String nombre;
  final String marca;
  final String unidad;
  final double precioUsd;
  final double stockMinimo;
  final int activo;

  Product({
    required this.codigo,
    this.codigoBarras = '',
    required this.nombre,
    this.marca = '',
    this.unidad = 'Unidad',
    required this.precioUsd,
    this.stockMinimo = 0,
    this.activo = 1,
  });

  Map<String, dynamic> toMap() => {
        'codigo': codigo,
        'codigo_barras': codigoBarras,
        'nombre': nombre,
        'marca': marca,
        'unidad': unidad,
        'precio_usd': precioUsd,
        'stock_minimo': stockMinimo,
        'activo': activo,
      };

  factory Product.fromMap(Map<String, dynamic> map) => Product(
        codigo: map['codigo']?.toString() ?? '',
        codigoBarras: map['codigo_barras']?.toString() ?? '',
        nombre: map['nombre']?.toString() ?? '',
        marca: map['marca']?.toString() ?? '',
        unidad: map['unidad']?.toString() ?? 'Unidad',
        precioUsd: double.tryParse(map['precio_usd']?.toString() ?? '0') ?? 0,
        stockMinimo: double.tryParse(map['stock_minimo']?.toString() ?? '0') ?? 0,
        activo: int.tryParse(map['activo']?.toString() ?? '1') ?? 1,
      );
}

class InventoryMovement {
  final String id;
  final String productoCodigo;
  final String tipo; // entrada, salida, ajuste
  final double cantidad;
  final double costoUsd;
  final String motivo;
  final String fecha;

  InventoryMovement({
    required this.id,
    required this.productoCodigo,
    required this.tipo,
    required this.cantidad,
    this.costoUsd = 0,
    this.motivo = '',
    required this.fecha,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'producto_codigo': productoCodigo,
        'tipo': tipo,
        'cantidad': cantidad,
        'costo_usd': costoUsd,
        'motivo': motivo,
        'fecha': fecha,
      };

  factory InventoryMovement.fromMap(Map<String, dynamic> map) => InventoryMovement(
        id: map['id']?.toString() ?? '',
        productoCodigo: map['producto_codigo']?.toString() ?? '',
        tipo: map['tipo']?.toString() ?? 'entrada',
        cantidad: double.tryParse(map['cantidad']?.toString() ?? '0') ?? 0,
        costoUsd: double.tryParse(map['costo_usd']?.toString() ?? '0') ?? 0,
        motivo: map['motivo']?.toString() ?? '',
        fecha: map['fecha']?.toString() ?? DateTime.now().toIso8601String(),
      );
}

class SaleItem {
  final String codigo;
  final String nombre;
  final double cantidad;
  final double precioUsd;

  SaleItem({
    required this.codigo,
    required this.nombre,
    required this.cantidad,
    required this.precioUsd,
  });

  Map<String, dynamic> toMap() => {
        'codigo': codigo,
        'nombre': nombre,
        'cantidad': cantidad,
        'precio_usd': precioUsd,
      };

  factory SaleItem.fromMap(Map<String, dynamic> map) => SaleItem(
        codigo: map['codigo']?.toString() ?? '',
        nombre: map['nombre']?.toString() ?? '',
        cantidad: double.tryParse(map['cantidad']?.toString() ?? '0') ?? 0,
        precioUsd: double.tryParse(map['precio_usd']?.toString() ?? '0') ?? 0,
      );
}

class PagoMixtoDetalle {
  final double divisasUsd;
  final double divisasBs;
  final double efectivoBs;
  final double pagoMovilBs;
  final double tarjetaBs;
  final double fiadoBs;
  final double totalAbonadoBs;
  final double vueltoBs;
  final double vueltoUsd;

  PagoMixtoDetalle({
    this.divisasUsd = 0,
    this.divisasBs = 0,
    this.efectivoBs = 0,
    this.pagoMovilBs = 0,
    this.tarjetaBs = 0,
    this.fiadoBs = 0,
    this.totalAbonadoBs = 0,
    this.vueltoBs = 0,
    this.vueltoUsd = 0,
  });

  Map<String, dynamic> toMap() => {
        'divisas_usd': divisasUsd,
        'divisas_bs': divisasBs,
        'efectivo_bs': efectivoBs,
        'pago_movil_bs': pagoMovilBs,
        'tarjeta_bs': tarjetaBs,
        'fiado_bs': fiadoBs,
        'total_abonado_bs': totalAbonadoBs,
        'vuelto_bs': vueltoBs,
        'vuelto_usd': vueltoUsd,
      };

  factory PagoMixtoDetalle.fromMap(Map<String, dynamic> map) => PagoMixtoDetalle(
        divisasUsd: double.tryParse(map['divisas_usd']?.toString() ?? '0') ?? 0,
        divisasBs: double.tryParse(map['divisas_bs']?.toString() ?? '0') ?? 0,
        efectivoBs: double.tryParse(map['efectivo_bs']?.toString() ?? '0') ?? 0,
        pagoMovilBs: double.tryParse(map['pago_movil_bs']?.toString() ?? '0') ?? 0,
        tarjetaBs: double.tryParse(map['tarjeta_bs']?.toString() ?? '0') ?? 0,
        fiadoBs: double.tryParse(map['fiado_bs']?.toString() ?? '0') ?? 0,
        totalAbonadoBs: double.tryParse(map['total_abonado_bs']?.toString() ?? '0') ?? 0,
        vueltoBs: double.tryParse(map['vuelto_bs']?.toString() ?? '0') ?? 0,
        vueltoUsd: double.tryParse(map['vuelto_usd']?.toString() ?? '0') ?? 0,
      );

  bool get tieneFiado => fiadoBs > 0;
  bool get tieneDivisas => divisasUsd > 0;
}

class Sale {
  final String id;
  final String numeroFactura;
  final double tasa;
  final double totalUsd;
  final double totalBs;
  final String metodoPago;
  final double? montoRecibidoBs;
  final double? montoRecibidoUsd;
  final double vueltoBs;
  final double vueltoUsd;
  final String? clienteNombre;
  final bool esFiada;
  final double saldoPendiente;
  final String fecha;
  final List<SaleItem> productos;
  final PagoMixtoDetalle? pagosDetalle;

  Sale({
    required this.id,
    required this.numeroFactura,
    required this.tasa,
    required this.totalUsd,
    required this.totalBs,
    required this.metodoPago,
    this.montoRecibidoBs,
    this.montoRecibidoUsd,
    this.vueltoBs = 0,
    this.vueltoUsd = 0,
    this.clienteNombre,
    this.esFiada = false,
    this.saldoPendiente = 0,
    required this.fecha,
    required this.productos,
    this.pagosDetalle,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'numero_factura': numeroFactura,
        'tasa': tasa,
        'total_usd': totalUsd,
        'total_bs': totalBs,
        'metodo_pago': metodoPago,
        'monto_recibido_bs': montoRecibidoBs,
        'monto_recibido_usd': montoRecibidoUsd,
        'vuelto_bs': vueltoBs,
        'vuelto_usd': vueltoUsd,
        'cliente_nombre': clienteNombre,
        'es_fiada': esFiada,
        'saldo_pendiente': saldoPendiente,
        'fecha': fecha,
        'productos': productos.map((p) => p.toMap()).toList(),
        'pagos_detalle': pagosDetalle?.toMap(),
      };

  factory Sale.fromMap(Map<String, dynamic> map) {
    var rawItems = map['productos'];
    List<SaleItem> items = [];
    if (rawItems is List) {
      items = rawItems.map((e) => SaleItem.fromMap(Map<String, dynamic>.from(e))).toList();
    }
    PagoMixtoDetalle? pagosDetalle;
    if (map['pagos_detalle'] != null) {
      pagosDetalle = PagoMixtoDetalle.fromMap(Map<String, dynamic>.from(map['pagos_detalle']));
    }
    return Sale(
      id: map['id']?.toString() ?? '',
      numeroFactura: map['numero_factura']?.toString() ?? '',
      tasa: double.tryParse(map['tasa']?.toString() ?? '1') ?? 1,
      totalUsd: double.tryParse(map['total_usd']?.toString() ?? '0') ?? 0,
      totalBs: double.tryParse(map['total_bs']?.toString() ?? '0') ?? 0,
      metodoPago: map['metodo_pago']?.toString() ?? 'efectivo',
      montoRecibidoBs: map['monto_recibido_bs'] != null ? double.tryParse(map['monto_recibido_bs'].toString()) : null,
      montoRecibidoUsd: map['monto_recibido_usd'] != null ? double.tryParse(map['monto_recibido_usd'].toString()) : null,
      vueltoBs: double.tryParse(map['vuelto_bs']?.toString() ?? '0') ?? 0,
      vueltoUsd: double.tryParse(map['vuelto_usd']?.toString() ?? '0') ?? 0,
      clienteNombre: map['cliente_nombre']?.toString(),
      esFiada: map['es_fiada'] == true || map['es_fiada'] == 1,
      saldoPendiente: double.tryParse(map['saldo_pendiente']?.toString() ?? '0') ?? 0,
      fecha: map['fecha']?.toString() ?? DateTime.now().toIso8601String(),
      productos: items,
      pagosDetalle: pagosDetalle,
    );
  }
}
