import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/design_tokens.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';
import '../widgets/states.dart';
import '../utils.dart';
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
          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
          title: Text('Stock: ${p.nombre}', style: DesignTokens.style('titleLarge')),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: DesignTokens.paddingAll('md'),
                  decoration: BoxDecoration(
                    color: DesignTokens.primaryContainer,
                    borderRadius: DesignTokens.borderRadius('md'),
                    border: Border.all(color: DesignTokens.primaryLight),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.inventory_2_rounded, color: DesignTokens.primaryDark),
                      DesignTokens.spaceMd.width,
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Stock Actual Disponible',
                            style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.primaryDark),
                          ),
                          Text(
                            '${currentStock.toStringAsFixed(2)} ${p.unidad}',
                            style: DesignTokens.style('titleMedium').copyWith(
                              fontWeight: FontWeight.bold,
                              color: DesignTokens.primaryDark,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: selectedType,
                  decoration: InputDecoration(
                    labelText: 'Tipo de operación',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'entrada', child: Text('📥 Entrada de Stock (+)')),
                    DropdownMenuItem(value: 'ajuste', child: Text('⚖️ Ajuste de Stock (+ o -)')),
                  ],
                  onChanged: (val) {
                    selectedType = val ?? 'entrada';
                    reason = selectedType == 'entrada' ? 'Entrada de mercancía' : 'Ajuste por conteo físico';
                  },
                ),
                DesignTokens.spaceMd.height,
                TextField(
                  controller: qtyCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(
                    labelText: selectedType == 'entrada' ? 'Cantidad a ingresar (+)' : 'Cantidad (+ sumar / - restar)',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: reason,
                  decoration: InputDecoration(
                    labelText: 'Motivo',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: motives.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                  onChanged: (val) => reason = val ?? motives.first,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                final qty = double.tryParse(qtyCtrl.text.replaceAll(',', '.')) ?? 0;
                if (qty == 0) {
                  showErrorDialog(context, title: 'Cantidad inválida', message: 'Ingresa una cantidad distinta de cero.');
                  return;
                }
                if (selectedType == 'entrada' && qty < 0) {
                  showErrorDialog(context, title: 'Cantidad inválida', message: 'Una entrada debe ser una cantidad positiva.');
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

                Navigator.pop(context);
                showSuccessDialog(context, title: 'Listo', message: 'Stock de ${p.nombre} actualizado.');
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
    showConfirmDialog(
      context,
      title: 'Eliminar Producto',
      message: '¿Estás seguro de que deseas eliminar "${p.nombre}"?',
      confirmLabel: 'Eliminar',
      cancelLabel: 'Cancelar',
      isDestructive: true,
    ).then((confirmed) {
      if (confirmed) {
        widget.state.queueEvent('producto_eliminado', {'codigo': p.codigo});
        showSuccessDialog(context, title: 'Eliminado', message: 'Producto "${p.nombre}" eliminado.');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final query = _searchController.text.trim().toLowerCase();
    final activeProducts = widget.state.products.values
        .where((p) => p.activo == 1 && (query.isEmpty || p.nombre.toLowerCase().contains(query) || p.codigo.toLowerCase().contains(query) || p.categoria.toLowerCase().contains(query) || p.proveedor.toLowerCase().contains(query)))
        .toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Inventario y Productos', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
      ),
      body: Column(
        children: [
          Card(
            margin: DesignTokens.paddingAll('md'),
            elevation: 0,
            color: DesignTokens.surface,
            shape: RoundedRectangleBorder(
              borderRadius: DesignTokens.borderRadius('lg'),
              side: BorderSide(color: DesignTokens.border),
            ),
            child: TextField(
              controller: _searchController,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                hintText: 'Buscar por nombre o código...',
                prefixIcon: Icon(Icons.search_rounded, color: DesignTokens.primary),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_searchController.text.isNotEmpty)
                      IconButton(
                        icon: Icon(Icons.clear, color: DesignTokens.textMuted),
                        onPressed: () => setState(() => _searchController.clear()),
                      ),
                    IconButton(
                      icon: Icon(Icons.qr_code_scanner_rounded, color: DesignTokens.primary),
                      tooltip: 'Escanear código de barras',
                      onPressed: () async {
                        final result = await Navigator.push(
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
                            setState(() => _searchController.text = code);
                          }
                        }
                      },
                    ),
                  ],
                ),
                contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                border: OutlineInputBorder(
                  borderRadius: DesignTokens.borderRadius('md'),
                  borderSide: BorderSide.none,
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: DesignTokens.borderRadius('md'),
                  borderSide: BorderSide(color: DesignTokens.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: DesignTokens.borderRadius('md'),
                  borderSide: BorderSide(color: DesignTokens.primary, width: 2),
                ),
                filled: true,
                fillColor: DesignTokens.surfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: activeProducts.isEmpty
                ? EmptyState(
                    icon: Icons.inventory_2_outlined,
                    title: 'No hay productos',
                    message: query.isEmpty
                        ? 'Agrega tu primer producto para empezar'
                        : 'No se encontraron productos con "$query"',
                    actionLabel: query.isEmpty ? 'Agregar Producto' : null,
                    onAction: query.isEmpty ? _showProductDialog : null,
                  )
                : ListView.builder(
                    padding: DesignTokens.paddingAll('md'),
                    itemCount: activeProducts.length,
                    itemBuilder: (ctx, i) {
                      final p = activeProducts[i];
                      final stock = widget.state.calculateStock(p.codigo);
                      final isLowStock = stock <= p.stockMinimo;
                      final priceBs = widget.state.calculateSalePriceBs(p.precioUsd);
                      final priceUsd = widget.state.calculateSalePriceUsd(p.precioUsd);

                      return Card(
                        elevation: 0,
                        margin: DesignTokens.paddingOnly(bottom: 'sm'),
                        shape: RoundedRectangleBorder(
                          borderRadius: DesignTokens.borderRadius('lg'),
                          side: BorderSide(
                            color: isLowStock ? DesignTokens.warningLight : DesignTokens.border,
                            width: isLowStock ? 1.5 : 1,
                          ),
                        ),
                        color: DesignTokens.surface,
                        child: InkWell(
                          borderRadius: DesignTokens.borderRadius('lg'),
                          onTap: () => _showStockAdjustDialog(p),
                          child: Padding(
                            padding: DesignTokens.paddingAll('md'),
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
                                              style: DesignTokens.style('titleSmall').copyWith(
                                                fontWeight: FontWeight.bold,
                                              ),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          if (p.marca.isNotEmpty) ...[
                                            DesignTokens.spaceSm.width,
                                            Text(
                                              '(${p.marca})',
                                              style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                            ),
                                          ],
                                        ],
                                      ),
                                      DesignTokens.spaceXs.height,
                                      Text(
                                        '${p.codigo} · Por ${p.unidad}${p.categoria.isNotEmpty ? ' · ${p.categoria}' : ''}${p.proveedor.isNotEmpty ? ' · Prov: ${p.proveedor}' : ''}',
                                        style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                      ),
                                      DesignTokens.spaceXs.height,
                                      Container(
                                        padding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
                                        decoration: BoxDecoration(
                                          color: isLowStock ? DesignTokens.warningContainer : DesignTokens.surfaceVariant,
                                          borderRadius: DesignTokens.borderRadius('sm'),
                                        ),
                                        child: Text(
                                          'Stock: ${stock.toStringAsFixed(2)} ${p.unidad} ${isLowStock ? '⚠' : ''}',
                                          style: DesignTokens.style('labelSmall').copyWith(
                                            fontWeight: FontWeight.bold,
                                            color: isLowStock ? DesignTokens.warning : DesignTokens.textSecondary,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                DesignTokens.spaceSm.width,
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      'Bs ${_currencyFormat.format(priceBs)}',
                                      style: DesignTokens.style('titleMedium').copyWith(
                                        fontWeight: FontWeight.bold,
                                        color: DesignTokens.primaryDark,
                                      ),
                                    ),
                                    Text(
                                      '\$${_currencyFormat.format(priceUsd)} USD',
                                      style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                    ),
                                    DesignTokens.spaceXs.height,
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        IconButton(
                                          tooltip: 'Ajustar Stock',
                                          icon: Icon(Icons.add_box_outlined, size: 20, color: DesignTokens.success),
                                          onPressed: () => _showStockAdjustDialog(p),
                                        ),
                                        IconButton(
                                          tooltip: 'Editar',
                                          icon: Icon(Icons.edit_outlined, size: 20, color: DesignTokens.primary),
                                          onPressed: () => _showProductDialog(p),
                                        ),
                                        IconButton(
                                          tooltip: 'Eliminar',
                                          icon: Icon(Icons.delete_outline, size: 20, color: DesignTokens.error),
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
        backgroundColor: DesignTokens.primary,
        foregroundColor: DesignTokens.textOnPrimary,
        icon: const Icon(Icons.add_rounded),
        label: Text('Nuevo Producto', style: DesignTokens.style('labelLarge')),
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
  final categoriaCtrl = TextEditingController(text: productToEdit?.categoria ?? '');
  final proveedorCtrl = TextEditingController(text: productToEdit?.proveedor ?? '');
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
        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
        title: Text(isEditing ? 'Modificar Producto' : 'Nuevo Producto', style: DesignTokens.style('titleLarge')),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: InputDecoration(
                  labelText: 'Nombre del producto *',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              DesignTokens.spaceMd.height,
              TextField(
                controller: brandCtrl,
                decoration: InputDecoration(
                  labelText: 'Marca (opcional)',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              DesignTokens.spaceMd.height,
              TextField(
                controller: categoriaCtrl,
                decoration: InputDecoration(
                  labelText: 'Categoría (opcional)',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              DesignTokens.spaceMd.height,
              TextField(
                controller: proveedorCtrl,
                decoration: InputDecoration(
                  labelText: 'Proveedor (opcional)',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              DesignTokens.spaceMd.height,
              DropdownButtonFormField<String>(
                value: selectedUnit,
                decoration: InputDecoration(
                  labelText: 'Unidad de venta',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
                items: kUnidades.map((u) => DropdownMenuItem(value: u, child: Text(u))).toList(),
                onChanged: (val) => setModalState(() => selectedUnit = val ?? 'Unidad'),
              ),
              DesignTokens.spaceMd.height,
              TextField(
                controller: barcodeCtrl,
                decoration: InputDecoration(
                  labelText: 'Código de Barras (será el código del producto)',
                  hintText: 'Escanea o escribe · ej: 7591234567890',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              DesignTokens.spaceMd.height,
              TextField(
                controller: priceCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: 'Precio base en USD (\$)',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                ),
              ),
              if (!isEditing) ...[
                DesignTokens.spaceMd.height,
                TextField(
                  controller: initialStockCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Stock Inicial (Existencia actual)',
                    hintText: '0 para empezar sin inventario',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                ),
              ],
              DesignTokens.spaceMd.height,
              TextField(
                controller: minStockCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: 'Stock mínimo para alertas',
                  border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
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
                showErrorDialog(context, title: 'Datos incompletos', message: 'Ingresa nombre y un precio mayor a cero.');
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
                'categoria': categoriaCtrl.text.trim(),
                'proveedor': proveedorCtrl.text.trim(),
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
                categoria: categoriaCtrl.text.trim(),
                proveedor: proveedorCtrl.text.trim(),
                unidad: selectedUnit,
                precioUsd: price,
                stockMinimo: minStock,
                activo: 1,
              );

              Navigator.pop(context);
              showSuccessDialog(context, title: 'Guardado', message: 'Producto $name guardado correctamente.');
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    ),
  );
  return resultado;
}