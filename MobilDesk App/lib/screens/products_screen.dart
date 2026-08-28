import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import 'scanner_screen.dart';

const List<String> kUnidades = [
  'Unidad',
  'Kg',
  'g',
  'L',
  'ml',
  'Paquete',
  'Caja',
  'Bulto',
  'Docena',
  'Metro',
];

class ProductsScreen extends StatefulWidget {
  final AppState state;
  const ProductsScreen({super.key, required this.state});

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  final _searchController = TextEditingController();
  final _currencyFormat = NumberFormat('#,##0.00', 'es_VE');

  void _showStockAdjustDialog(Product p) {
    final currentStock = widget.state.calculateStock(p.codigo);
    final qtyCtrl = TextEditingController();
    String selectedType = 'entrada';
    String reason = 'Entrada de mercancía';

    final motives = [
      'Entrada de mercancía',
      'Compra a proveedor',
      'Ajuste por conteo físico',
      'Producto dañado',
      'Producto vencido',
      'Pérdida / Merma',
      'Devolución',
      'Otro',
    ];

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text('Stock: ${p.nombre}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.inventory_2_rounded, color: Color(0xFF1D4ED8)),
                      const SizedBox(width: 10),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Stock Actual Disponible', style: TextStyle(fontSize: 12, color: Color(0xFF1E40AF))),
                          Text(
                            '${currentStock.toStringAsFixed(2)} ${p.unidad}',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E3A8A)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: selectedType,
                  decoration: const InputDecoration(labelText: 'Tipo de operación', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'entrada', child: Text('📥 Entrada de Stock (+)')),
                    DropdownMenuItem(value: 'ajuste', child: Text('⚖️ï¸ Ajuste de Stock (+ o -)')),
                  ],
                  onChanged: (val) => setModalState(() {
                    selectedType = val ?? 'entrada';
                    reason = selectedType == 'entrada' ? 'Entrada de mercancía' : 'Ajuste por conteo físico';
                  }),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: qtyCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(
                    labelText: selectedType == 'entrada' ? 'Cantidad a ingresar (+)' : 'Cantidad (+ sumar / - restar)',
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: reason,
                  decoration: const InputDecoration(labelText: 'Motivo', border: OutlineInputBorder()),
                  items: motives.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                  onChanged: (val) => setModalState(() => reason = val ?? motives.first),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                final qty = double.tryParse(qtyCtrl.text.replaceAll(',', '.')) ?? 0;
                if (qty == 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Ingresa una cantidad distinta de cero.')),
                  );
                  return;
                }
                if (selectedType == 'entrada' && qty < 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Una entrada debe ser una cantidad positiva.')),
                  );
                  return;
                }

                widget.state.queueEvent('movimiento_inventario', {
                  'producto_codigo': p.codigo,
                  'tipo': selectedType,
                  'cantidad': qty,
                  'costo_usd': 0,
                  'motivo': reason,
                  'fecha': DateTime.now().toIso8601String(),
                });

                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Stock de ${p.nombre} actualizado.')),
                );
              },
              child: const Text('Guardar'),
            ),
          ],
        ),
      ),
    );
  }

  void _showProductDialog([Product? productToEdit]) async {
    final result = await showProductFormDialog(context, widget.state, productToEdit: productToEdit);
    if (result != null) setState(() {});
  }


  void _deleteProduct(Product p) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar Producto'),
        content: Text('¿Estás seguro de que deseas eliminar "${p.nombre}"?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              widget.state.queueEvent('producto_eliminado', {'codigo': p.codigo});
              Navigator.pop(ctx);
            },
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final query = _searchController.text.trim().toLowerCase();
    final activeProducts = widget.state.products.values
        .where((p) => p.activo == 1 && (query.isEmpty || p.nombre.toLowerCase().contains(query) || p.codigo.toLowerCase().contains(query)))
        .toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: const Text('Inventario y Productos', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: TextField(
              controller: _searchController,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                hintText: 'Buscar por nombre o código...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_searchController.text.isNotEmpty)
                      IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () => setState(() => _searchController.clear()),
                      ),
                    IconButton(
                      icon: const Icon(Icons.qr_code_scanner_rounded, color: Color(0xFF2563EB)),
                      tooltip: 'Escanear código de barras',
                      onPressed: () async {
                        final result = await Navigator.push<dynamic>(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const ScannerScreen(
                              allowMultiScan: false,
                              title: 'Buscar Producto',
                            ),
                          ),
                        );
                        if (result != null) {
                          final code = result is String ? result : (result is List && result.isNotEmpty ? result.first.toString() : '');
                          if (code.isNotEmpty) {
                            setState(() {
                              _searchController.text = code;
                            });
                          }
                        }
                      },
                    ),
                  ],
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
          Expanded(
            child: activeProducts.isEmpty
                ? const Center(
                    child: Text(
                      'No se encontraron productos.',
                      style: TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: activeProducts.length,
                    itemBuilder: (ctx, i) {
                      final p = activeProducts[i];
                      final stock = widget.state.calculateStock(p.codigo);
                      final isLowStock = stock <= p.stockMinimo;
                      final priceBs = widget.state.calculateSalePriceBs(p.precioUsd);
                      final priceUsd = widget.state.calculateSalePriceUsd(p.precioUsd);

                      return Card(
                        elevation: 0,
                        margin: const EdgeInsets.only(bottom: 8),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(color: isLowStock ? const Color(0xFFFDE68A) : const Color(0xFFE2E8F0)),
                        ),
                        color: Colors.white,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () => _showStockAdjustDialog(p),
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              p.nombre,
                                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          if (p.marca.isNotEmpty) ...[
                                            const SizedBox(width: 6),
                                            Text(
                                              '(${p.marca})',
                                              style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                                            ),
                                          ],
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        '${p.codigo} · Por ${p.unidad}',
                                        style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                                      ),
                                      const SizedBox(height: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: isLowStock ? const Color(0xFFFEF3C7) : const Color(0xFFF1F5F9),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          'Stock: ${stock.toStringAsFixed(2)} ${p.unidad} ${isLowStock ? '⚠️ï¸' : ''}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                            color: isLowStock ? const Color(0xFFB45309) : const Color(0xFF475569),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      'Bs ${_currencyFormat.format(priceBs)}',
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1E3A8A)),
                                    ),
                                    Text(
                                      '\$${_currencyFormat.format(priceUsd)} USD',
                                      style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        IconButton(
                                          tooltip: 'Ajustar Stock',
                                          icon: const Icon(Icons.add_box_outlined, size: 20, color: Color(0xFF059669)),
                                          onPressed: () => _showStockAdjustDialog(p),
                                        ),
                                        IconButton(
                                          tooltip: 'Editar',
                                          icon: const Icon(Icons.edit_outlined, size: 20, color: Color(0xFF2563EB)),
                                          onPressed: () => _showProductDialog(p),
                                        ),
                                        IconButton(
                                          tooltip: 'Eliminar',
                                          icon: const Icon(Icons.delete_outline, size: 20, color: Colors.red),
                                          onPressed: () => _deleteProduct(p),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF2563EB),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Nuevo Producto'),
        onPressed: () => _showProductDialog(),
      ),
    );
  }
}

/// Formulario de producto compartido (Inventario y POS).
/// [preloadedBarcode] precarga el codigo de barras (flujo escanear-para-crear).
/// Retorna el producto guardado o null si se cancelo.
Future<Product?> showProductFormDialog(
  BuildContext context,
  AppState state, {
  Product? productToEdit,
  String? preloadedBarcode,
}) async {
  final isEditing = productToEdit != null;
  final nameCtrl = TextEditingController(text: productToEdit?.nombre ?? '');
  final brandCtrl = TextEditingController(text: productToEdit?.marca ?? '');
  final priceCtrl = TextEditingController(text: productToEdit != null ? productToEdit.precioUsd.toString() : '');
  final minStockCtrl = TextEditingController(text: productToEdit != null ? productToEdit.stockMinimo.toString() : '0');
  final initialStockCtrl = TextEditingController(text: '0');
  final barcodeCtrl = TextEditingController(
      text: productToEdit?.codigoBarras ?? (preloadedBarcode ?? ''));
  String selectedUnit = productToEdit?.unidad ?? 'Unidad';

  String generarCodigo() {
    int maxNum = 0;
    for (final p in state.products.values) {
      final digits = RegExp(r'\d+').firstMatch(p.codigo)?.group(0);
      final n = int.tryParse(digits ?? '') ?? 0;
      if (n > maxNum) maxNum = n;
    }
    for (final m in state.movements) {
      final digits = RegExp(r'\d+').firstMatch(m.productoCodigo)?.group(0);
      final n = int.tryParse(digits ?? '') ?? 0;
      if (n > maxNum) maxNum = n;
    }
    return 'P${(maxNum + 1).toString().padLeft(6, '0')}';
  }

  Product? resultado;
  await showDialog(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setModalState) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(isEditing ? 'Modificar Producto' : 'Nuevo Producto'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Nombre del producto *',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: brandCtrl,
                decoration: const InputDecoration(
                  labelText: 'Marca (opcional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: selectedUnit,
                decoration: const InputDecoration(
                  labelText: 'Unidad de venta',
                  border: OutlineInputBorder(),
                ),
                items: kUnidades.map((u) => DropdownMenuItem(value: u, child: Text(u))).toList(),
                onChanged: (val) => setModalState(() => selectedUnit = val ?? 'Unidad'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: barcodeCtrl,
                decoration: const InputDecoration(
                  labelText: 'Código de Barras (será el código del producto)',
                  hintText: 'Escanea o escribe · ej: 7591234567890',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: priceCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Precio base en USD (\$)',
                  border: OutlineInputBorder(),
                ),
              ),
              if (!isEditing) ...[
                const SizedBox(height: 10),
                TextField(
                  controller: initialStockCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Stock Inicial (Existencia actual)',
                    hintText: '0 para empezar sin inventario',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
              const SizedBox(height: 10),
              TextField(
                controller: minStockCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Stock mínimo para alertas',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              final name = nameCtrl.text.trim();
              final price = double.tryParse(priceCtrl.text.replaceAll(',', '.')) ?? 0;
              final minStock = double.tryParse(minStockCtrl.text.replaceAll(',', '.')) ?? 0;
              final initStock = double.tryParse(initialStockCtrl.text.replaceAll(',', '.')) ?? 0;

              if (name.isEmpty || price <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Ingresa nombre y un precio mayor a cero.')),
                );
                return;
              }

              // El codigo de barras escaneado ES el codigo del producto.
              final barcodeText = barcodeCtrl.text.trim();
              final code = isEditing
                  ? productToEdit.codigo
                  : (barcodeText.isNotEmpty ? barcodeText : generarCodigo());

              if (!isEditing) {
                state.movements.removeWhere((m) => m.productoCodigo == code);
              }

              final productData = {
                'codigo': code,
                'codigo_barras': barcodeText.isNotEmpty ? barcodeText : code,
                'nombre': name,
                'marca': brandCtrl.text.trim(),
                'unidad': selectedUnit,
                'precio_usd': price,
                'stock_minimo': minStock,
                'activo': 1,
              };

              state.queueEvent('producto_guardado', productData);

              if (!isEditing && initStock > 0) {
                state.queueEvent('movimiento_inventario', {
                  'producto_codigo': code,
                  'tipo': 'entrada',
                  'cantidad': initStock,
                  'costo_usd': 0,
                  'motivo': 'Inventario inicial',
                  'fecha': DateTime.now().toIso8601String(),
                });
              }

              resultado = Product(
                codigo: code,
                codigoBarras: barcodeText.isNotEmpty ? barcodeText : code,
                nombre: name,
                marca: brandCtrl.text.trim(),
                unidad: selectedUnit,
                precioUsd: price,
                stockMinimo: minStock,
                activo: 1,
              );

              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Producto $name guardado correctamente.')),
              );
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    ),
  );
  return resultado;
}
