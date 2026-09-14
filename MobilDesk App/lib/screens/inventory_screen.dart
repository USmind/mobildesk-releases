import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';
import '../widgets/states.dart';
import '../utils.dart';

class InventoryScreen extends StatefulWidget {
  final AppState state;
  const InventoryScreen({super.key, required this.state});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _showMovementDialog() {
    final activeProducts = widget.state.products.values.where((p) => p.activo == 1).toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));

    if (activeProducts.isEmpty) {
      showErrorDialog(
        context,
        title: 'Sin productos',
        message: 'Primero debes crear al menos un producto.',
      );
      return;
    }

    Product selectedProduct = activeProducts.first;
    String selectedType = 'entrada';
    final qtyCtrl = TextEditingController();
    final reasonCtrl = TextEditingController(text: 'Compra de mercancía');

    final motives = [
      'Compra de mercancía',
      'Producto dañado',
      'Producto vencido',
      'Pérdida',
      'Ajuste de inventario',
      'Devolución',
      'Corrección de inventario',
      'Otro',
    ];

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
          title: Text('Movimiento de Inventario', style: DesignTokens.style('titleLarge')),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<Product>(
                  value: selectedProduct,
                  isExpanded: true,
                  decoration: InputDecoration(
                    labelText: 'Producto',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: activeProducts.map((p) => DropdownMenuItem(value: p, child: Text('${p.nombre} (${p.codigo})'))).toList(),
                  onChanged: (val) => setModalState(() => selectedProduct = val ?? selectedProduct),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: selectedType,
                  decoration: InputDecoration(
                    labelText: 'Tipo de movimiento',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'entrada', child: Text('Entrada de mercancía (+)')),
                    DropdownMenuItem(value: 'ajuste', child: Text('Ajuste de inventario')),
                  ],
                  onChanged: (val) => setModalState(() => selectedType = val ?? 'entrada'),
                ),
                DesignTokens.spaceMd.height,
                TextField(
                  controller: qtyCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(
                    labelText: selectedType == 'entrada' ? 'Cantidad a ingresar' : 'Cantidad (positiva o negativa)',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: motives.contains(reasonCtrl.text) ? reasonCtrl.text : motives.first,
                  decoration: InputDecoration(
                    labelText: 'Motivo',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: motives.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                  onChanged: (val) => setModalState(() => reasonCtrl.text = val ?? motives.first),
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
                  showErrorDialog(context, title: 'Cantidad inválida', message: 'La cantidad no puede ser cero.');
                  return;
                }
                if (selectedType == 'entrada' && qty < 0) {
                  showErrorDialog(context, title: 'Cantidad inválida', message: 'Una entrada debe tener cantidad positiva.');
                  return;
                }

                final movementData = {
                  'producto_codigo': selectedProduct.codigo,
                  'tipo': selectedType,
                  'cantidad': qty,
                  'costo_usd': 0,
                  'motivo': reasonCtrl.text.trim(),
                  'fecha': DateTime.now().toIso8601String(),
                };

                widget.state.queueEvent('movimiento_inventario', movementData);
                Navigator.pop(context);
                showSuccessDialog(context, title: 'Guardado', message: 'Movimiento de inventario registrado.');
              },
              child: const Text('Guardar'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final activeProducts = widget.state.products.values.where((p) => p.activo == 1).toList()
      ..sort((a, b) => a.nombre.compareTo(b.nombre));

    final movements = widget.state.movements.reversed.toList();

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Gestión de Inventario', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: DesignTokens.textOnPrimary,
          unselectedLabelColor: DesignTokens.primaryLight,
          indicatorColor: DesignTokens.textOnPrimary,
          tabs: [
            Tab(icon: Icon(Icons.inventory_rounded, size: 20), text: 'Existencias'),
            Tab(icon: Icon(Icons.history_rounded, size: 20), text: 'Movimientos'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Existencias
          activeProducts.isEmpty
              ? EmptyState(
                  icon: Icons.inventory_2_outlined,
                  title: 'Sin productos',
                  message: 'Agrega productos para gestionar existencias',
                  actionLabel: 'Agregar Producto',
                  onAction: () {
                    // Navigate to products screen via MainNavigationScreen
                    _tabController.animateTo(1); // This would need navigation logic
                  },
                )
              : ListView.builder(
                  padding: DesignTokens.paddingAll('md'),
                  itemCount: activeProducts.length,
                  itemBuilder: (ctx, i) {
                    final p = activeProducts[i];
                    final stock = widget.state.calculateStock(p.codigo);
                    final isLow = stock <= p.stockMinimo;

                    return Card(
                      elevation: 0,
                      margin: DesignTokens.paddingOnly(bottom: 'sm'),
                      shape: RoundedRectangleBorder(
                        borderRadius: DesignTokens.borderRadius('lg'),
                        side: BorderSide(
                          color: isLow ? DesignTokens.warningLight : DesignTokens.border,
                          width: isLow ? 1.5 : 1,
                        ),
                      ),
                      color: DesignTokens.surface,
                      child: ListTile(
                        title: Text(p.nombre, style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold)),
                        subtitle: Text(
                          '${p.codigo} · Min: ${p.stockMinimo.toStringAsFixed(1)} ${p.unidad}',
                          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                        ),
                        trailing: Container(
                          padding: DesignTokens.paddingSymmetric(h: 'md', v: 'xs'),
                          decoration: BoxDecoration(
                            color: isLow ? DesignTokens.warningContainer : DesignTokens.primaryContainer,
                            borderRadius: DesignTokens.borderRadius('md'),
                          ),
                          child: Text(
                            '${stock.toStringAsFixed(2)} ${p.unidad}',
                            style: DesignTokens.style('bodyMedium').copyWith(
                              fontWeight: FontWeight.bold,
                              color: isLow ? DesignTokens.warning : DesignTokens.primaryDark,
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),

          // Tab 2: Movimientos
          movements.isEmpty
              ? EmptyState(
                  icon: Icons.history_outlined,
                  title: 'Sin movimientos',
                  message: 'Los movimientos aparecerán aquí al registrar entradas o ajustes',
                )
              : ListView.builder(
                  padding: DesignTokens.paddingAll('md'),
                  itemCount: movements.length,
                  itemBuilder: (ctx, i) {
                    final m = movements[i];
                    final isPositive = m.tipo == 'entrada' || m.cantidad > 0;

                    return Card(
                      elevation: 0,
                      margin: DesignTokens.paddingOnly(bottom: 'sm'),
                      shape: RoundedRectangleBorder(
                        borderRadius: DesignTokens.borderRadius('lg'),
                        side: BorderSide(color: DesignTokens.border),
                      ),
                      color: DesignTokens.surface,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: isPositive ? DesignTokens.successContainer : DesignTokens.errorContainer,
                          child: Icon(
                            isPositive ? Icons.arrow_downward_rounded : Icons.arrow_upward_rounded,
                            color: isPositive ? DesignTokens.success : DesignTokens.error,
                            size: 20,
                          ),
                        ),
                        title: Text(
                          '${m.productoCodigo} · ${m.tipo.toUpperCase()}',
                          style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          '${m.motivo} · ${m.fecha.split('T').first}',
                          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                        ),
                        trailing: Text(
                          '${isPositive ? '+' : ''}${m.cantidad.toStringAsFixed(2)}',
                          style: DesignTokens.style('titleSmall').copyWith(
                            fontWeight: FontWeight.bold,
                            color: isPositive ? DesignTokens.success : DesignTokens.error,
                          ),
                        ),
                      ),
                    );
                  },
                ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        icon: const Icon(Icons.add_rounded),
        label: Text('Registrar Movimiento', style: DesignTokens.style('labelLarge')),
        onPressed: _showMovementDialog,
      ),
    );
  }
}