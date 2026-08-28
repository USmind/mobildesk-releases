import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/app_state.dart';

class SalesHistoryScreen extends StatefulWidget {
  final AppState state;
  const SalesHistoryScreen({super.key, required this.state});

  @override
  State<SalesHistoryScreen> createState() => _SalesHistoryScreenState();
}

class _SalesHistoryScreenState extends State<SalesHistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _currencyFormat = NumberFormat('#,##0.00', 'es_VE');

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

  void _registerDebtPayment(Sale sale) {
    final amountCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Registrar Pago de Deuda'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Cliente: ${sale.clienteNombre ?? "Sin nombre"}', style: const TextStyle(fontWeight: FontWeight.bold)),
            Text('Factura: #${sale.numeroFactura}'),
            Text('Saldo Pendiente: Bs ${_currencyFormat.format(sale.saldoPendiente)}', style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            TextField(
              controller: amountCtrl,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Monto recibido en Bs',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () {
              final amount = double.tryParse(amountCtrl.text.replaceAll(',', '.')) ?? 0;
              if (amount <= 0 || amount > sale.saldoPendiente) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('El monto debe ser mayor a cero y no superar el saldo.')),
                );
                return;
              }

              widget.state.recordDebtPayment(sale.id, amount);

              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Pago registrado correctamente.')),
              );
            },
            child: const Text('Guardar Pago'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final allSales = widget.state.sales.reversed.toList();
    final creditSales = widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0).toList().reversed.toList();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: const Text('Historial de Ventas', style: TextStyle(fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFF93C5FD),
          indicatorColor: Colors.white,
          tabs: [
            Tab(text: 'Ventas (${allSales.length})'),
            Tab(text: 'Fiados / Deudas (${creditSales.length})'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Todas las ventas
          allSales.isEmpty
              ? const Center(child: Text('No hay ventas registradas.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: allSales.length,
                  itemBuilder: (ctx, i) {
                    final sale = allSales[i];
                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: Color(0xFFE2E8F0)),
                      ),
                      color: Colors.white,
                      child: ListTile(
                        title: Text('Factura #${sale.numeroFactura}', style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(
                          '${sale.fecha.split('T').first} · ${sale.metodoPago.toUpperCase()}'
                          '${sale.clienteNombre != null ? " · Cliente: ${sale.clienteNombre}" : ""}',
                          style: const TextStyle(fontSize: 12),
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              'Bs ${_currencyFormat.format(sale.totalBs)}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                            Text(
                              '\$${_currencyFormat.format(sale.totalUsd)}',
                              style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),

          // Tab 2: Fiados
          creditSales.isEmpty
              ? const Center(child: Text('No hay cuentas por cobrar pendientes.'))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: creditSales.length,
                  itemBuilder: (ctx, i) {
                    final sale = creditSales[i];
                    return Card(
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: Color(0xFFFED7AA)),
                      ),
                      color: Colors.white,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    sale.clienteNombre ?? 'Cliente',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                  ),
                                  const SizedBox(height: 2),
                                  Text('Factura #${sale.numeroFactura} · Total: Bs ${_currencyFormat.format(sale.totalBs)}', style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Saldo Pendiente: Bs ${_currencyFormat.format(sale.saldoPendiente)}',
                                    style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFEA580C), fontSize: 13),
                                  ),
                                ],
                              ),
                            ),
                            FilledButton(
                              style: FilledButton.styleFrom(
                                backgroundColor: const Color(0xFF0F766E),
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                              onPressed: () => _registerDebtPayment(sale),
                              child: const Text('Abonar', style: TextStyle(fontSize: 12)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ],
      ),
    );
  }
}
