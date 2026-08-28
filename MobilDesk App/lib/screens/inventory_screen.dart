import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/app_state.dart';

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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Primero debes crear al menos un producto.')),
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
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Movimiento de Inventario'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<Product>(
                  initialValue: selectedProduct,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Producto', border: OutlineInputBorder()),
                  items: activeProducts.map((p) => DropdownMenuItem(value: p, child: Text('${p.nombre} (${p.codigo})'))).toList(),
                  onChanged: (val) => setModalState(() => selectedProduct = val ?? selectedProduct),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: selectedType,
                  decoration: const InputDecoration(labelText: 'Tipo de movimiento', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'entrada', child: Text('Entrada de mercancía (+)')),
                    DropdownMenuItem(value: 'ajuste', child: Text('Ajuste de inventario')),
                  ],
                  onChanged: (val) => setModalState(() => selectedType = val ?? 'entrada'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: qtyCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                  decoration: InputDecoration(
                    labelText: selectedType == 'entrada' ? 'Cantidad a ingresar' : 'Cantidad (positiva o negativa)',
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: motives.contains(reasonCtrl.text) ? reasonCtrl.text : motives.first,
                  decoration: const InputDecoration(labelText: 'Motivo', border: OutlineInputBorder()),
                  items: motives.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
                  onChanged: (val) => setModalState(() => reasonCtrl.text = val ?? motives.first),
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
                    const SnackBar(content: Text('La cantidad no puede ser cero.')),
                  );
                  return;
                }
                if (selectedType == 'entrada' && qty < 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Una entrada debe tener cantidad positiva.')),
                  );
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
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Movimiento de inventario guardado.')),
                );
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
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: const Text('Gestión de Inventario', style: TextStyle(fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFF93C5FD),
          indicatorColor: Colors.white,
          tabs: const [
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
              ? const Center(child: Text('No hay productos registrados.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: activeProducts.length,
                  itemBuilder: (ctx, i) {
                    final p = activeProducts[i];
                    final stock = widget.state.calculateStock(p.codigo);
                    final isLow = stock <= p.stockMinimo;

                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: BorderSide(color: isLow ? const Color(0xFFFDE68A) : const Color(0xFFE2E8F0)),
                      ),
                      color: Colors.white,
                      child: ListTile(
                        title: Text(p.nombre, style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text('${p.codigo} · Min: ${p.stockMinimo.toStringAsFixed(1)} ${p.unidad}'),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: isLow ? const Color(0xFFFEF3C7) : const Color(0xFFEFF6FF),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '${stock.toStringAsFixed(2)} ${p.unidad}',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: isLow ? const Color(0xFFB45309) : const Color(0xFF1D4ED8),
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),

          // Tab 2: Movimientos
          movements.isEmpty
              ? const Center(child: Text('No hay movimientos registrados.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: movements.length,
                  itemBuilder: (ctx, i) {
                    final m = movements[i];
                    final isPositive = m.tipo == 'entrada' || m.cantidad > 0;

                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: Color(0xFFE2E8F0)),
                      ),
                      color: Colors.white,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: isPositive ? const Color(0xFFECFDF5) : const Color(0xFFFEF2F2),
                          child: Icon(
                            isPositive ? Icons.arrow_downward_rounded : Icons.arrow_upward_rounded,
                            color: isPositive ? const Color(0xFF059669) : const Color(0xFFDC2626),
                            size: 20,
                          ),
                        ),
                        title: Text('${m.productoCodigo} · ${m.tipo.toUpperCase()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        subtitle: Text('${m.motivo} · ${m.fecha.split('T').first}', style: const TextStyle(fontSize: 12)),
                        trailing: Text(
                          '${isPositive ? '+' : ''}${m.cantidad.toStringAsFixed(2)}',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: isPositive ? const Color(0xFF059669) : const Color(0xFFDC2626),
                          ),
                        ),
                      ),
                    );
                  },
                ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF0F766E),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Registrar Movimiento'),
        onPressed: _showMovementDialog,
      ),
    );
  }
}
