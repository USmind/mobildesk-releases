import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/app_state.dart';
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
  String _paymentMethod = 'efectivo';
  PagoMixtoDetalle? _mixedPaymentDetalle;

  final List<SaleItem> _cart = [];

  void _addToCart() {
    if (_selectedProduct == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona un producto primero.')),
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
      _selectedProduct = null;
      _quantityController.text = '1';
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
          backgroundColor: const Color(0xFF16A34A),
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
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Producto no registrado'),
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
            backgroundColor: const Color(0xFFDC2626),
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
        title: const Row(
          children: [
            Icon(Icons.check_circle_rounded, color: Color(0xFF16A34A), size: 28),
            SizedBox(width: 8),
            Text('Venta Registrada'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Factura: $invoiceNumber', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text('Total: Bs ${_currencyFormat.format(_totalBs)} (\$${_currencyFormat.format(_totalUsd)})'),
            Text('Método: ${_paymentMethod.toUpperCase()}'),
            if (isMixto && _mixedPaymentDetalle != null) ...[
              const SizedBox(height: 8),
              const Text('Desglose de Pago:', style: TextStyle(fontWeight: FontWeight.bold)),
              if (_mixedPaymentDetalle!.divisasUsd > 0)
                Text('  • Divisas: \$${_currencyFormat.format(_mixedPaymentDetalle!.divisasUsd)} (Bs ${_currencyFormat.format(_mixedPaymentDetalle!.divisasBs)})'),
              if (_mixedPaymentDetalle!.efectivoBs > 0)
                Text('  • Efectivo: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.efectivoBs)}'),
              if (_mixedPaymentDetalle!.pagoMovilBs > 0)
                Text('  • Pago Móvil: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.pagoMovilBs)}'),
              if (_mixedPaymentDetalle!.tarjetaBs > 0)
                Text('  • Tarjeta: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.tarjetaBs)}'),
              if (_mixedPaymentDetalle!.fiadoBs > 0)
                Text('  • Fiado: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.fiadoBs)}'),
              const SizedBox(height: 4),
              if (_mixedPaymentDetalle!.vueltoBs > 0)
                Text('Vuelto: Bs ${_currencyFormat.format(_mixedPaymentDetalle!.vueltoBs)} (USD \$${_currencyFormat.format(_mixedPaymentDetalle!.vueltoUsd)})', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF16A34A))),
            ],
            if (!isMixto && _paymentMethod == 'efectivo')
              Text('Vuelto: Bs ${_currencyFormat.format(_vueltoBs)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF16A34A))),
            if (!isMixto && _paymentMethod == 'divisas')
              Text('Vuelto: \$${_currencyFormat.format(_vueltoUsd)} (Bs ${_currencyFormat.format(_vueltoUsd * widget.state.exchangeRate)})', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF16A34A))),
            if (isFiado || (isMixto && _mixedPaymentDetalle!.fiadoBs > 0))
              Text('Deuda Cliente: ${clientName.isNotEmpty ? clientName : 'Sin nombre'}', style: const TextStyle(color: Color(0xFFD97706), fontWeight: FontWeight.bold)),
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
            child: const Text('Nueva Venta'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final activeProducts = widget.state.products.values.where((p) => p.activo == 1).toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: const Text('Nueva Venta', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // Selector de Producto
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<Product>(
                        initialValue: _selectedProduct,
                        isExpanded: true,
                        hint: const Text('Seleccionar producto...'),
                        decoration: InputDecoration(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: activeProducts.map((p) {
                          final stock = widget.state.calculateStock(p.codigo);
                          final priceBs = widget.state.calculateSalePriceBs(p.precioUsd);
                          return DropdownMenuItem(
                            value: p,
                            child: Text(
                              '${p.nombre} (${p.codigo}) - Bs ${_currencyFormat.format(priceBs)} [Stock: ${stock.toStringAsFixed(1)}]',
                              style: const TextStyle(fontSize: 13),
                              overflow: TextOverflow.ellipsis,
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedProduct = val;
                          });
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton.filled(
                      tooltip: 'Escanear código',
                      onPressed: _scanBarcode,
                      icon: const Icon(Icons.qr_code_scanner_rounded),
                      style: IconButton.styleFrom(
                        backgroundColor: const Color(0xFF0F172A),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.all(12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: _quantityController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: 'Cantidad',
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 3,
                      child: FilledButton.icon(
                        onPressed: _addToCart,
                        icon: const Icon(Icons.add_shopping_cart_rounded, size: 18),
                        label: const Text('Agregar'),
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFF2563EB),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
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
                ? const Center(
                    child: Text(
                      'No hay productos agregados a la venta.',
                      style: TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _cart.length,
                    itemBuilder: (ctx, i) {
                      final item = _cart[i];
                      final subtotalUsd = item.cantidad * item.precioUsd;
                      final subtotalBs = subtotalUsd * widget.state.exchangeRate;

                      return Card(
                        elevation: 0,
                        margin: const EdgeInsets.only(bottom: 8),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                          side: const BorderSide(color: Color(0xFFE2E8F0)),
                        ),
                        color: Colors.white,
                        child: ListTile(
                          title: Text(item.nombre, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          subtitle: Text(
                            '${item.cantidad.toStringAsFixed(2)} x \$${_currencyFormat.format(item.precioUsd)}',
                            style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
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
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                  Text(
                                    '\$${_currencyFormat.format(subtotalUsd)}',
                                    style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                                  ),
                                ],
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete_outline_rounded, color: Colors.red, size: 20),
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
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
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
                    const Text('TOTAL A COBRAR:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF475569))),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('Bs ${_currencyFormat.format(_totalBs)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 20, color: Color(0xFF1E3A8A))),
                        Text('\$${_currencyFormat.format(_totalUsd)} USD', style: const TextStyle(fontSize: 13, color: Color(0xFF64748B))),
                      ],
                    ),
                  ],
                ),
                const Divider(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: _paymentMethod,
                        decoration: InputDecoration(
                          labelText: 'Método de pago',
                          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'efectivo', child: Text('Efectivo')),
                          DropdownMenuItem(value: 'divisas', child: Text('Divisas USD')),
                          DropdownMenuItem(value: 'pago_movil', child: Text('Pago Móvil')),
                          DropdownMenuItem(value: 'tarjeta', child: Text('Tarjeta')),
                          DropdownMenuItem(value: 'fiado', child: Text('Fiado / Crédito')),
                          DropdownMenuItem(value: 'mixto', child: Text('🔀 Pago Mixto / Fraccionado')),
                        ],
                        onChanged: (val) => setState(() => _paymentMethod = val ?? 'efectivo'),
                      ),
                    ),
                    if (_paymentMethod == 'mixto') ...[
                      const SizedBox(width: 8),
                      FilledButton.icon(
                        onPressed: _openMixedPaymentDialog,
                        icon: const Icon(Icons.account_balance_wallet_rounded, size: 18),
                        label: const Text('Configurar'),
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFF2563EB),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                      ),
                    ] else if (_paymentMethod == 'efectivo' || _paymentMethod == 'divisas') ...[
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _receivedController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          onChanged: (_) => setState(() {}),
                          decoration: InputDecoration(
                            labelText: _paymentMethod == 'efectivo' ? 'Recibido (Bs)' : 'Recibido (USD)',
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                if (_paymentMethod == 'efectivo' && _vueltoBs > 0) ...[
                  const SizedBox(height: 6),
                  Text('Vuelto: Bs ${_currencyFormat.format(_vueltoBs)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF16A34A), fontSize: 14)),
                ],
                if (_paymentMethod == 'divisas' && _vueltoUsd > 0) ...[
                  const SizedBox(height: 6),
                  Text('Vuelto: \$${_currencyFormat.format(_vueltoUsd)} (Bs ${_currencyFormat.format(_vueltoUsd * widget.state.exchangeRate)})', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF16A34A), fontSize: 14)),
                ],
                if (_paymentMethod == 'fiado') ...[
                  const SizedBox(height: 8),
                  TextField(
                    controller: _clientNameController,
                    decoration: InputDecoration(
                      labelText: 'Nombre del Cliente (Obligatorio)',
                      prefixIcon: const Icon(Icons.person_outline, size: 18),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _cart.isEmpty ? null : _checkout,
                    icon: const Icon(Icons.check_circle_outline_rounded),
                    label: const Text('Registrar Venta', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF16A34A),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
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
