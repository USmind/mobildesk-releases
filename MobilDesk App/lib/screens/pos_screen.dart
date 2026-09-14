import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/design_tokens.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';
import '../widgets/states.dart';
import '../utils.dart';
import 'scanner_screen.dart';
import 'products_screen.dart' show showProductFormDialog;
import '../widgets/mixed_payment_dialog.dart';

class PosScreen extends StatefulWidget {
  final AppState state;
  const PosScreen({super.key, required this.state});

  @override
  State<PosScreen> createState() => _PosScreenState();
}

class _PosScreenState extends State<PosScreen> {
  final _currencyFormat = NumberFormat('#,##0.00', 'es_VE');

  Product? _selectedProduct;
  final _quantityController = TextEditingController(text: '1');
  final _receivedController = TextEditingController();
  final _clientNameController = TextEditingController();
  final _productSearchController = TextEditingController();
  final _searchFocusNode = FocusNode();
  String _paymentMethod = 'efectivo';
  PagoMixtoDetalle? _mixedPaymentDetalle;

  final List<SaleItem> _cart = [];

  @override
  void initState() {
    super.initState();
    _consumirClienteParaFiar();
    _clientNameController.addListener(() => setState(() {}));
  }

  /// Si viene de Cobrar/Fiados con "Agregar a su cuenta", precarga el cliente.
  void _consumirClienteParaFiar() {
    final pending = widget.state.clienteParaFiar;
    if (pending != null && pending.trim().isNotEmpty) {
      _clientNameController.text = pending.trim();
      _paymentMethod = 'fiado';
      widget.state.clienteParaFiar = null;
    }
  }

  /// Deudas agrupadas por cliente para sugerir al escribir (nombre normalizado).
  Map<String, Map<String, dynamic>> _deudasAgrupadas() {
    final map = <String, Map<String, dynamic>>{};
    for (final s in widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0)) {
      final raw = (s.clienteNombre ?? 'Sin nombre').trim();
      final key = raw.toLowerCase();
      final entry = map.putIfAbsent(key, () => {'nombre': raw, 'total': 0.0, 'facturas': 0});
      entry['total'] = (entry['total'] as double) + s.saldoPendiente;
      entry['facturas'] = (entry['facturas'] as int) + 1;
    }
    return map;
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _receivedController.dispose();
    _clientNameController.dispose();
    _productSearchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  /// Productos activos que coinciden con la búsqueda (nombre, código, barras o marca).
  List<Product> _matchProducts(String query) {
    final active = widget.state.products.values.where((p) => p.activo == 1).toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return active;
    return active
        .where((p) =>
            p.nombre.toLowerCase().contains(q) ||
            p.codigo.toLowerCase().contains(q) ||
            p.codigoBarras.toLowerCase().contains(q) ||
            p.marca.toLowerCase().contains(q))
        .toList();
  }

  void _addToCart() {
    if (_selectedProduct == null) {
      // Si lo escrito coincide exacto con un solo producto, elegirlo directo.
      final q = _productSearchController.text.trim();
      if (q.isNotEmpty) {
        final ql = q.toLowerCase();
        final exact = _matchProducts(q)
            .where((p) =>
                p.codigo.toLowerCase() == ql ||
                p.codigoBarras.toLowerCase() == ql ||
                p.nombre.toLowerCase() == ql)
            .toList();
        if (exact.length == 1) {
          setState(() => _selectedProduct = exact.first);
        }
      }
    }
    if (_selectedProduct == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Busca y toca un producto de la lista.')),
      );
      return;
    }

    final qty = double.tryParse(_quantityController.text.replaceAll(',', '.')) ?? 0;
    if (qty <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('La cantidad debe ser mayor a cero.')),
      );
      return;
    }

    final stock = widget.state.calculateStock(_selectedProduct!.codigo);
    final inCartQty = _cart.where((i) => i.codigo == _selectedProduct!.codigo).fold<double>(0, (sum, i) => sum + i.cantidad);

    if (qty + inCartQty > stock) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Stock insuficiente. Disponible: ${stock.toStringAsFixed(2)}')),
      );
      return;
    }

    final unitPriceUsd = widget.state.calculateSalePriceUsd(_selectedProduct!.precioUsd);

    final keptProduct = _selectedProduct;
    setState(() {
      final existingIndex = _cart.indexWhere((i) => i.codigo == _selectedProduct!.codigo);
      if (existingIndex >= 0) {
        final old = _cart[existingIndex];
        _cart[existingIndex] = SaleItem(
          codigo: old.codigo,
          nombre: old.nombre,
          cantidad: old.cantidad + qty,
          precioUsd: unitPriceUsd,
        );
      } else {
        _cart.add(SaleItem(
          codigo: _selectedProduct!.codigo,
          nombre: _selectedProduct!.nombre,
          cantidad: qty,
          precioUsd: unitPriceUsd,
        ));
      }
      // Mantener el producto seleccionado para agregar rápido de nuevo.
      _selectedProduct = keptProduct;
      _quantityController.text = '1';
    });
    // Devolver el foco al buscador para el siguiente agregado.
    _searchFocusNode.requestFocus();
  }

  void _incrementCartItem(int index) {
    final item = _cart[index];
    final stock = widget.state.calculateStock(item.codigo);
    final totalInCart = _cart.where((e) => e.codigo == item.codigo).fold<double>(0, (s, e) => s + e.cantidad);
    if (totalInCart + 1 > stock) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Stock insuficiente. Disponible: ${stock.toStringAsFixed(2)}')),
      );
      return;
    }
    setState(() {
      _cart[index] = SaleItem(
        codigo: item.codigo,
        nombre: item.nombre,
        cantidad: item.cantidad + 1,
        precioUsd: item.precioUsd,
      );
    });
  }

  void _decrementCartItem(int index) {
    final item = _cart[index];
    setState(() {
      if (item.cantidad > 1) {
        _cart[index] = SaleItem(
          codigo: item.codigo,
          nombre: item.nombre,
          cantidad: item.cantidad - 1,
          precioUsd: item.precioUsd,
        );
      } else {
        _cart.removeAt(index);
      }
    });
  }

  void _removeFromCart(int index) {
    setState(() {
      _cart.removeAt(index);
    });
  }

  Future<void> _scanBarcode() async {
    final result = await Navigator.push<dynamic>(
      context,
      MaterialPageRoute(
        builder: (_) => const ScannerScreen(
          allowMultiScan: true,
          title: 'Escanear para Venta',
        ),
      ),
    );
    if (result == null) return;

    List<String> codes = [];
    if (result is List<String>) {
      codes = result;
    } else if (result is List) {
      codes = result.map((e) => e.toString()).toList();
    } else if (result is String && result.trim().isNotEmpty) {
      codes = [result.trim()];
    }

    if (codes.isEmpty) return;

    int addedCount = 0;
    for (final code in codes) {
      final added = await _processScannedCode(code);
      if (added) addedCount++;
    }

    if (codes.length > 1 && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: DesignTokens.success,
              content: Text('✅ $addedCount productos agregados al carrito de venta'),
            ),
      );
    }
  }

  Future<bool> _processScannedCode(String code) async {
    final normalized = code.trim().toLowerCase();
    Product? found;
    for (final p in widget.state.products.values) {
      if (p.activo != 1) continue;
      final codigoBarrasLower = p.codigoBarras.toLowerCase();
      if (codigoBarrasLower == normalized) {
        found = p;
        break;
      }
      if (p.codigo.toLowerCase() == normalized) {
        found = p;
        break;
      }
    }

    if (found == null) {
      if (!mounted) return false;
      final crear = await showDialog<bool>(
        context: context,
        builder: (dCtx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
          title: Text('Producto no registrado', style: DesignTokens.style('titleLarge')),
          content: Text('No existe un producto con el código:\n$code\n\n¿Deseas registrarlo ahora?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dCtx, false), child: const Text('No')),
            FilledButton(onPressed: () => Navigator.pop(dCtx, true), child: const Text('Sí, crear')),
          ],
        ),
      );
      if (crear != true || !mounted) return false;
      final nuevo = await showProductFormDialog(context, widget.state, preloadedBarcode: code);
      if (nuevo == null || !mounted) return false;
      setState(() {
        _selectedProduct = nuevo;
        _productSearchController.text = nuevo.nombre;
        _quantityController.text = '1';
      });
      _addToCart();
      return true;
    }

    // Add directly to cart
    final stock = widget.state.calculateStock(found.codigo);
    final inCartIndex = _cart.indexWhere((i) => i.codigo == found!.codigo);
    final inCartQty = inCartIndex >= 0 ? _cart[inCartIndex].cantidad : 0.0;

    if (1.0 + inCartQty > stock) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: DesignTokens.error,
            content: Text('Stock insuficiente para ${found.nombre}. Disponible: ${stock.toStringAsFixed(2)}'),
          ),
        );
      }
      return false;
    }

    final unitPriceUsd = widget.state.calculateSalePriceUsd(found.precioUsd);
    setState(() {
      if (inCartIndex >= 0) {
        final old = _cart[inCartIndex];
        _cart[inCartIndex] = SaleItem(
          codigo: old.codigo,
          nombre: old.nombre,
          cantidad: old.cantidad + 1.0,
          precioUsd: unitPriceUsd,
        );
      } else {
        _cart.add(SaleItem(
          codigo: found!.codigo,
          nombre: found.nombre,
          cantidad: 1.0,
          precioUsd: unitPriceUsd,
        ));
      }
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          duration: const Duration(seconds: 1),
          content: Text('➕ ${found.nombre} agregado al carrito'),
        ),
      );
    }
    return true;
  }

  double get _totalUsd => _cart.fold<double>(0, (sum, item) => sum + (item.cantidad * item.precioUsd));
  double get _totalBs => _totalUsd * widget.state.exchangeRate;

  double get _vueltoBs {
    if (_paymentMethod != 'efectivo') return 0;
    final rec = double.tryParse(_receivedController.text.replaceAll(',', '.')) ?? 0;
    return rec > _totalBs ? rec - _totalBs : 0;
  }

  double get _vueltoUsd {
    if (_paymentMethod != 'divisas') return 0;
    final rec = double.tryParse(_receivedController.text.replaceAll(',', '.')) ?? 0;
    return rec > _totalUsd ? rec - _totalUsd : 0;
  }

  void _openMixedPaymentDialog() {
    showDialog<PagoMixtoDetalle>(
      context: context,
      builder: (_) => MixedPaymentDialog(
        totalBs: _totalBs,
        totalUsd: _totalUsd,
        tasa: widget.state.exchangeRate,
        onConfirm: (detalle) {
          setState(() {
            _mixedPaymentDetalle = detalle;
          });
        },
      ),
    ).then((detalle) {
      if (detalle != null && _mixedPaymentDetalle == null) {
        setState(() {
          _mixedPaymentDetalle = detalle;
        });
      }
    });
  }

  void _checkout() {
    if (_cart.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Agrega al menos un producto a la venta.')),
      );
      return;
    }

    final isFiado = _paymentMethod == 'fiado';
    final isMixto = _paymentMethod == 'mixto';
    final clientName = _clientNameController.text.trim();
    if (isFiado && clientName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Para ventas fiadas debes ingresar el nombre del cliente.')),
      );
      return;
    }
    if (isMixto && _mixedPaymentDetalle == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Configura el pago mixto antes de registrar la venta.')),
      );
      return;
    }

    double? montoRecibidoBs;
    double? montoRecibidoUsd;
    double vueltoBs = 0;
    double vueltoUsd = 0;
    double saldoPendiente = 0;

    if (isMixto && _mixedPaymentDetalle != null) {
      final pd = _mixedPaymentDetalle!;
      montoRecibidoBs = pd.totalAbonadoBs;
      montoRecibidoUsd = pd.divisasUsd;
      vueltoBs = pd.vueltoBs;
      vueltoUsd = pd.vueltoUsd;
      saldoPendiente = pd.fiadoBs;
    } else if (_paymentMethod == 'efectivo') {
      final rec = double.tryParse(_receivedController.text.replaceAll(',', '.')) ?? 0;
      if (rec < _totalBs) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('El monto en efectivo recibido no cubre el total.')),
        );
        return;
      }
      montoRecibidoBs = rec;
      vueltoBs = _vueltoBs;
    } else if (_paymentMethod == 'divisas') {
      final rec = double.tryParse(_receivedController.text.replaceAll(',', '.')) ?? 0;
      if (rec < _totalUsd) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('El monto en divisas recibido no cubre el total.')),
        );
        return;
      }
      montoRecibidoUsd = rec;
      vueltoUsd = _vueltoUsd;
    } else if (isFiado) {
      saldoPendiente = _totalBs;
    }

    final invoiceNumber = 'MOV-${DateTime.now().millisecondsSinceEpoch.toString().substring(5)}';

    final saleData = {
      'numero_factura': invoiceNumber,
      'tasa': widget.state.exchangeRate,
      'total_usd': _totalUsd,
      'total_bs': _totalBs,
      'metodo_pago': _paymentMethod,
      'monto_recibido_bs': montoRecibidoBs,
      'monto_recibido_usd': montoRecibidoUsd,
      'vuelto_bs': vueltoBs,
      'vuelto_usd': vueltoUsd,
      'cliente_nombre': clientName.isNotEmpty ? clientName : null,
      'es_fiada': isFiado || (isMixto && _mixedPaymentDetalle!.fiadoBs > 0),
      'saldo_pendiente': saldoPendiente,
      'fecha': DateTime.now().toIso8601String(),
      'productos': _cart.map((i) => i.toMap()).toList(),
      if (isMixto && _mixedPaymentDetalle != null) 'pagos_detalle': _mixedPaymentDetalle!.toMap(),
    };

    widget.state.queueEvent('venta_registrada', saleData);

    for (final item in _cart) {
      widget.state.queueEvent('movimiento_inventario', {
        'producto_codigo': item.codigo,
        'tipo': 'salida',
        'cantidad': item.cantidad,
        'costo_usd': 0,
        'motivo': 'Venta móvil #$invoiceNumber',
        'fecha': DateTime.now().toIso8601String(),
      });
    }

    // Show confirmation dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
        title: Row(
          children: [
            Icon(Icons.check_circle_rounded, color: DesignTokens.success, size: 28),
            DesignTokens.spaceMd.width,
            Text('Venta Registrada', style: DesignTokens.style('titleLarge')),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Factura: $invoiceNumber', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
            DesignTokens.spaceXs.height,
            Text('Total: Bs ${_currencyFormat.format(_totalBs)} (\$${_currencyFormat.format(_totalUsd)})', style: DesignTokens.style('bodyMedium')),
            Text('Método: ${_paymentMethod.toUpperCase()}', style: DesignTokens.style('bodyMedium')),
            if (isMixto && _mixedPaymentDetalle != null) ...[
              DesignTokens.spaceSm.height,
              Text('Desglose de Pago:', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
              if (_mixedPaymentDetalle!.divisasUsd > 0)
                Text('  • Divisas: \$${_currencyFormat.format(_mixedPaymentDetalle!.divisasUsd)} (Bs ${_currencyFormat.format(_mixedPaymentDetalle!.divisasBs)})', style: DesignTokens.style('bodySmall')),
              if (_mixedPaymentDetalle!.efectivoBs > 0)
                Text('  • Efectivo: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.efectivoBs)}', style: DesignTokens.style('bodySmall')),
              if (_mixedPaymentDetalle!.pagoMovilBs > 0)
                Text('  • Pago Móvil: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.pagoMovilBs)}', style: DesignTokens.style('bodySmall')),
              if (_mixedPaymentDetalle!.tarjetaBs > 0)
                Text('  • Tarjeta: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.tarjetaBs)}', style: DesignTokens.style('bodySmall')),
              if (_mixedPaymentDetalle!.fiadoBs > 0)
                Text('  • Fiado: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.fiadoBs)}', style: DesignTokens.style('bodySmall')),
              DesignTokens.spaceXs.height,
              if (_mixedPaymentDetalle!.vueltoBs > 0)
                Text('Vuelto: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.vueltoBs)} (USD \$${_currencyFormat.format(_mixedPaymentDetalle!.vueltoUsd)})', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.success)),
            ],
            if (!isMixto && _paymentMethod == 'efectivo')
              Text('Vuelto: Bs ${_currencyFormat.format(_vueltoBs)}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.success)),
            if (!isMixto && _paymentMethod == 'divisas')
              Text('Vuelto: \$${_currencyFormat.format(_vueltoUsd)} (Bs ${_currencyFormat.format(_vueltoUsd * widget.state.exchangeRate)})', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.success)),
            if (isFiado || (isMixto && _mixedPaymentDetalle!.fiadoBs > 0))
              Text('Deuda Cliente: ${clientName.isNotEmpty ? clientName : 'Sin nombre'}', style: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.warning, fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() {
                _cart.clear();
                _receivedController.clear();
                _clientNameController.clear();
                _mixedPaymentDetalle = null;
              });
            },
            child: Text('Nueva Venta', style: DesignTokens.style('labelLarge')),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Consumir "Agregar a su cuenta" aunque el State ya existiera.
    if (widget.state.clienteParaFiar != null && widget.state.clienteParaFiar!.trim().isNotEmpty) {
      _clientNameController.text = widget.state.clienteParaFiar!.trim();
      _paymentMethod = 'fiado';
      widget.state.clienteParaFiar = null;
    }
    final searchQuery = _productSearchController.text.trim().toLowerCase();
    final suggestions = searchQuery.isEmpty
        ? const <Product>[]
        : _matchProducts(searchQuery).take(6).toList();

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Nueva Venta', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
      ),
      body: Column(
        children: [
          // Selector de Producto
          Container(
            padding: DesignTokens.paddingAll('md'),
            color: DesignTokens.surface,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _productSearchController,
                        focusNode: _searchFocusNode,
                        onChanged: (_) => setState(() {
                          // Si edita el texto, la selección anterior ya no vale.
                          if (_selectedProduct != null &&
                              _productSearchController.text.trim().toLowerCase() !=
                                  _selectedProduct!.nombre.toLowerCase()) {
                            _selectedProduct = null;
                          }
                        }),
                        decoration: InputDecoration(
                          hintText: 'Buscar producto por nombre, código o marca...',
                          prefixIcon: Icon(Icons.search_rounded, color: DesignTokens.primary),
                          suffixIcon: _productSearchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () => setState(() {
                                    _productSearchController.clear();
                                    _selectedProduct = null;
                                  }),
                                )
                              : null,
                          contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                          border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                        ),
                      ),
                    ),
                    DesignTokens.spaceSm.width,
                    IconButton.filled(
                      tooltip: 'Escanear código',
                      onPressed: _scanBarcode,
                      icon: const Icon(Icons.qr_code_scanner_rounded),
                      style: IconButton.styleFrom(
                        backgroundColor: DesignTokens.secondaryDark,
                        foregroundColor: Colors.white,
                        padding: DesignTokens.paddingAll('md'),
                        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('md')),
                      ),
                    ),
                  ],
                ),
                if (_selectedProduct != null) ...[
                  DesignTokens.spaceSm.height,
                  Container(
                    padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                    decoration: BoxDecoration(
                      color: DesignTokens.primaryContainer,
                      borderRadius: DesignTokens.borderRadius('md'),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle_rounded, color: DesignTokens.primaryDark, size: 20),
                        DesignTokens.spaceSm.width,
                        Expanded(
                          child: Text(
                            '${_selectedProduct!.nombre} · Bs ${_currencyFormat.format(widget.state.calculateSalePriceBs(_selectedProduct!.precioUsd))} [Stock: ${widget.state.calculateStock(_selectedProduct!.codigo).toStringAsFixed(1)}]',
                            style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        IconButton(
                          tooltip: 'Quitar selección',
                          visualDensity: VisualDensity.compact,
                          icon: const Icon(Icons.close_rounded, size: 18),
                          onPressed: () => setState(() {
                            _selectedProduct = null;
                            _productSearchController.clear();
                          }),
                        ),
                      ],
                    ),
                  ),
                ] else if (suggestions.isNotEmpty) ...[
                  DesignTokens.spaceSm.height,
                  ...suggestions.map((p) {
                    final priceBs = widget.state.calculateSalePriceBs(p.precioUsd);
                    final stock = widget.state.calculateStock(p.codigo);
                    return InkWell(
                      onTap: () => setState(() {
                        _selectedProduct = p;
                        _productSearchController.text = p.nombre;
                      }),
                      child: Padding(
                        padding: DesignTokens.paddingSymmetric(v: 'sm'),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(p.nombre,
                                      style: DesignTokens.style('bodyMedium')
                                          .copyWith(fontWeight: FontWeight.bold),
                                      overflow: TextOverflow.ellipsis),
                                  Text('${p.codigo} · Bs ${_currencyFormat.format(priceBs)} · Stock: ${stock.toStringAsFixed(1)}',
                                      style: DesignTokens.style('bodySmall')
                                          .copyWith(color: DesignTokens.textSecondary)),
                                ],
                              ),
                            ),
                            Icon(Icons.add_circle_outline_rounded, color: DesignTokens.primary),
                          ],
                        ),
                      ),
                    );
                  }),
                ] else if (searchQuery.isNotEmpty) ...[
                  DesignTokens.spaceSm.height,
                  Text('Sin resultados para "$searchQuery". Prueba con otro nombre o código.',
                      style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
                ],
                DesignTokens.spaceSm.height,
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: _quantityController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: 'Cantidad',
                          contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                          border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                        ),
                      ),
                    ),
                    DesignTokens.spaceSm.width,
                    Expanded(
                      flex: 3,
                      child: FilledButton.icon(
                        onPressed: _addToCart,
                        icon: const Icon(Icons.add_shopping_cart_rounded, size: 18),
                        label: Text('Agregar', style: DesignTokens.style('labelLarge')),
                        style: FilledButton.styleFrom(
                          backgroundColor: DesignTokens.primary,
                          padding: DesignTokens.paddingSymmetric(h: 'md', v: 'md'),
                          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('md')),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Lista de Items en Carrito
          Expanded(
            child: _cart.isEmpty
                ? EmptyState(
                    icon: Icons.shopping_cart_outlined,
                    title: 'Carrito vacío',
                    message: 'Agrega productos para iniciar la venta',
                  )
                : ListView.builder(
                    padding: DesignTokens.paddingAll('md'),
                    itemCount: _cart.length,
                    itemBuilder: (ctx, i) {
                      final item = _cart[i];
                      final subtotalUsd = item.cantidad * item.precioUsd;
                      final subtotalBs = subtotalUsd * widget.state.exchangeRate;

                      return Card(
                        elevation: 0,
                        margin: DesignTokens.paddingOnly(bottom: 'sm'),
                        shape: RoundedRectangleBorder(
                          borderRadius: DesignTokens.borderRadius('md'),
                          side: BorderSide(color: DesignTokens.border),
                        ),
                        color: DesignTokens.surface,
                        child: ListTile(
                          title: Text(item.nombre, style: DesignTokens.style('titleSmall').copyWith(fontWeight: FontWeight.bold)),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${item.cantidad.toStringAsFixed(2)} x \$${_currencyFormat.format(item.precioUsd)}',
                                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textSecondary),
                              ),
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    tooltip: 'Quitar uno',
                                    visualDensity: VisualDensity.compact,
                                    icon: const Icon(Icons.remove_circle_outline, size: 22),
                                    onPressed: () => _decrementCartItem(i),
                                  ),
                                  Text(
                                    item.cantidad.toStringAsFixed(item.cantidad.truncateToDouble() == item.cantidad ? 0 : 2),
                                    style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold),
                                  ),
                                  IconButton(
                                    tooltip: 'Agregar uno',
                                    visualDensity: VisualDensity.compact,
                                    icon: const Icon(Icons.add_circle_outline, size: 22),
                                    onPressed: () => _incrementCartItem(i),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(
                                    'Bs ${_currencyFormat.format(subtotalBs)}',
                                    style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold),
                                  ),
                                  Text(
                                    '\$${_currencyFormat.format(subtotalUsd)}',
                                    style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textSecondary),
                                  ),
                                ],
                              ),
                              IconButton(
                                icon: Icon(Icons.delete_outline_rounded, color: DesignTokens.error, size: 20),
                                onPressed: () => _removeFromCart(i),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),

          // Panel de Pago y Total
          Container(
            padding: DesignTokens.paddingSymmetric(h: 'md', v: 'lg'),
            decoration: BoxDecoration(
              color: DesignTokens.surface,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              boxShadow: [
                BoxShadow(color: Colors.black.withAlpha(20), blurRadius: 10, offset: const Offset(0, -3)),
              ],
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(child: Text('TOTAL:', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textSecondary))),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('Bs ${_currencyFormat.format(_totalBs)}', style: DesignTokens.style('headlineSmall').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.primaryDark)),
                        Text('\$${_currencyFormat.format(_totalUsd)} USD', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textSecondary)),
                      ],
                    ),
                  ],
                ),
                const Divider(height: 20),
                DropdownButtonFormField<String>(
                  value: _paymentMethod,
                  isDense: true,
                  decoration: InputDecoration(
                    labelText: 'Método de pago',
                    contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'xs'),
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('sm')),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'efectivo', child: Text('Efectivo')),
                    DropdownMenuItem(value: 'divisas', child: Text('Divisas USD')),
                    DropdownMenuItem(value: 'pago_movil', child: Text('Pago Móvil')),
                    DropdownMenuItem(value: 'tarjeta', child: Text('Tarjeta')),
                    DropdownMenuItem(value: 'fiado', child: Text('Fiado / Crédito')),
                    DropdownMenuItem(value: 'mixto', child: Text('🔀 Pago Mixto')),
                  ],
                  onChanged: (val) => setState(() => _paymentMethod = val ?? 'efectivo'),
                ),
                if (_paymentMethod == 'mixto') ...[
                  DesignTokens.spaceSm.height,
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _openMixedPaymentDialog,
                      icon: const Icon(Icons.account_balance_wallet_rounded, size: 18),
                      label: Text('Configurar Pago Mixto', style: DesignTokens.style('labelLarge')),
                      style: FilledButton.styleFrom(
                        backgroundColor: DesignTokens.primary,
                        padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('sm')),
                      ),
                    ),
                  ),
                ],
                if (_paymentMethod == 'efectivo' || _paymentMethod == 'divisas') ...[
                  DesignTokens.spaceSm.height,
                  TextField(
                    controller: _receivedController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                      labelText: _paymentMethod == 'efectivo' ? 'Recibido (Bs)' : 'Recibido (USD)',
                      contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'xs'),
                      border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('sm')),
                    ),
                  ),
                ],
                if (_paymentMethod == 'efectivo' && _vueltoBs > 0) ...[
                  DesignTokens.spaceSm.height,
                  Text('Vuelto: Bs ${_currencyFormat.format(_vueltoBs)}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.success)),
                ],
                if (_paymentMethod == 'divisas' && _vueltoUsd > 0) ...[
                  DesignTokens.spaceSm.height,
                  Text('Vuelto: \$${_currencyFormat.format(_vueltoUsd)} (Bs ${_currencyFormat.format(_vueltoUsd * widget.state.exchangeRate)})', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.success)),
                ],
                if (_paymentMethod == 'fiado') ...[
                  DesignTokens.spaceSm.height,
                  TextField(
                    controller: _clientNameController,
                    decoration: InputDecoration(
                      labelText: 'Nombre del Cliente (Obligatorio)',
                      prefixIcon: const Icon(Icons.person_outline, size: 18),
                      contentPadding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
                      border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('sm')),
                    ),
                  ),
                  Builder(builder: (ctx) {
                    final agrupadas = _deudasAgrupadas();
                    if (agrupadas.isEmpty) return const SizedBox.shrink();
                    final typed = _clientNameController.text.trim().toLowerCase();
                    final sugeridos = agrupadas.entries
                        .where((e) => typed.isEmpty || (e.value['nombre'] as String).toLowerCase().contains(typed))
                        .take(4)
                        .toList();
                    if (sugeridos.isEmpty) return const SizedBox.shrink();
                    // Si lo escrito coincide exacto con un deudor, avisar que se sumará.
                    Widget? aviso;
                    if (typed.isNotEmpty && agrupadas.containsKey(typed)) {
                      final m = agrupadas[typed]!;
                      aviso = Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          '⚠️ ${m['nombre']} ya debe Bs ${_currencyFormat.format(m['total'])} en ${m['facturas']} factura(s). Lo nuevo se sumará a su misma cuenta.',
                          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.warning, fontWeight: FontWeight.bold),
                        ),
                      );
                    }
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (aviso != null) aviso,
                        const SizedBox(height: 6),
                        ...sugeridos.map((e) {
                          final m = e.value;
                          return InkWell(
                            onTap: () => setState(() => _clientNameController.text = m['nombre'] as String),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: Row(
                                children: [
                                  const Icon(Icons.history_rounded, size: 16),
                                  const SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      '${m['nombre']} — debe Bs ${_currencyFormat.format(m['total'])} (${m['facturas']} fac.)',
                                      style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textSecondary),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        }),
                      ],
                    );
                  }),
                ],
                DesignTokens.spaceMd.height,
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _cart.isEmpty ? null : _checkout,
                    icon: const Icon(Icons.check_circle_outline_rounded),
                    label: Text('Registrar Venta', style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold)),
                    style: FilledButton.styleFrom(
                      backgroundColor: DesignTokens.success,
                      padding: DesignTokens.paddingSymmetric(h: 'md', v: 'md'),
                      shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('md')),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
