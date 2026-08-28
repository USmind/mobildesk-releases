import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/app_state.dart';

class DashboardScreen extends StatelessWidget {
  final AppState state;
  final Function(int) onNavigateTab;

  const DashboardScreen({
    super.key,
    required this.state,
    required this.onNavigateTab,
  });

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat('#,##0.00', 'es_VE');
    final activeProducts = state.products.values.where((p) => p.activo == 1).toList();

    // Sales today
    final now = DateTime.now();
    final todayStr = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    final salesToday = state.sales.where((s) => s.fecha.startsWith(todayStr)).toList();
    final totalBsToday = salesToday.fold<double>(0, (sum, s) => sum + s.totalBs);
    final totalUsdToday = salesToday.fold<double>(0, (sum, s) => sum + s.totalUsd);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF172554),
        foregroundColor: Colors.white,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              state.businessName.toUpperCase(),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 0.5),
            ),
            const Text(
              'Panel de Control',
              style: TextStyle(fontSize: 12, color: Color(0xFF93C5FD)),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Sincronizar',
            icon: state.isSyncing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.sync_rounded),
            onPressed: state.isSyncing ? null : state.sync,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: state.sync,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Status Banner
            InkWell(
              onTap: state.isSyncing ? null : state.sync,
              borderRadius: BorderRadius.circular(10),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: state.syncStatus.contains('Sincronizado')
                      ? const Color(0xFFECFDF5)
                      : (state.syncStatus.contains('Error') || state.syncStatus.contains('vencida') || state.syncStatus.contains('Sin conexión'))
                          ? const Color(0xFFFEF2F2)
                          : const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: state.syncStatus.contains('Sincronizado')
                        ? const Color(0xFFA7F3D0)
                        : (state.syncStatus.contains('Error') || state.syncStatus.contains('vencida') || state.syncStatus.contains('Sin conexión'))
                            ? const Color(0xFFFECACA)
                            : const Color(0xFFBFDBFE),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      state.syncStatus.contains('Sincronizado')
                          ? Icons.cloud_done_rounded
                          : (state.syncStatus.contains('Error') || state.syncStatus.contains('vencida') || state.syncStatus.contains('Sin conexión'))
                              ? Icons.cloud_off_rounded
                              : Icons.sync_rounded,
                      size: 20,
                      color: state.syncStatus.contains('Sincronizado')
                          ? const Color(0xFF059669)
                          : (state.syncStatus.contains('Error') || state.syncStatus.contains('vencida') || state.syncStatus.contains('Sin conexión'))
                              ? const Color(0xFFDC2626)
                              : const Color(0xFF2563EB),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        state.syncStatus,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: state.syncStatus.contains('Sincronizado')
                              ? const Color(0xFF065F46)
                              : (state.syncStatus.contains('Error') || state.syncStatus.contains('vencida') || state.syncStatus.contains('Sin conexión'))
                                  ? const Color(0xFF991B1B)
                                  : const Color(0xFF1E40AF),
                        ),
                      ),
                    ),
                    if (state.outbox.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF59E0B),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '${state.outbox.length} pendientes',
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Tasa USD/Bs Banner
            Card(
              elevation: 0,
              color: const Color(0xFF1E3A8A),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: InkWell(
                onTap: () => _showQuickRateDialog(context, state),
                borderRadius: BorderRadius.circular(12),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    children: [
                      const Icon(Icons.currency_exchange_rounded, color: Colors.white, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Text(
                                  'TASA OFICIAL USD / BS',
                                  style: TextStyle(color: Color(0xFF93C5FD), fontSize: 11, fontWeight: FontWeight.bold),
                                ),
                                SizedBox(width: 6),
                                Icon(Icons.edit_rounded, color: Color(0xFF93C5FD), size: 12),
                              ],
                            ),
                            Text(
                              '1 USD = Bs ${currencyFormat.format(state.exchangeRate)}',
                              style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                      if (state.profitMargin > 0)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF2563EB),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '+${state.profitMargin.toStringAsFixed(0)}% ganancia',
                            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),

            // KPIs Grid
            Row(
              children: [
                Expanded(
                  child: _buildKpiCard(
                    title: 'VENTAS HOY',
                    mainValue: 'Bs ${currencyFormat.format(totalBsToday)}',
                    subValue: '\$${currencyFormat.format(totalUsdToday)} (${salesToday.length} ventas)',
                    color: const Color(0xFF0284C7),
                    icon: Icons.point_of_sale_rounded,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildKpiCard(
                    title: 'PRODUCTOS',
                    mainValue: '${activeProducts.length}',
                    subValue: 'Catálogo Activo',
                    color: const Color(0xFF16A34A),
                    icon: Icons.inventory_2_rounded,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Quick Action Shortcuts
            const Text(
              'Acciones Rápidas',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: _buildActionButton(
                    icon: Icons.add_shopping_cart_rounded,
                    label: 'Nueva Venta',
                    color: const Color(0xFF2563EB),
                    onTap: () => onNavigateTab(1), // Tab 1 is POS
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildActionButton(
                    icon: Icons.add_box_rounded,
                    label: 'Inventario',
                    color: const Color(0xFF0F766E),
                    onTap: () => onNavigateTab(3), // Tab 3 is Inventory
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Recent sales list
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Últimas Ventas Registradas',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
                ),
                TextButton(
                  onPressed: () => onNavigateTab(4), // Tab 4 is Sales History
                  child: const Text('Ver todas'),
                ),
              ],
            ),
            const SizedBox(height: 6),
            if (state.sales.isEmpty)
              Container(
                padding: const EdgeInsets.all(24),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: const Text(
                  'Aún no hay ventas registradas.\nPulsa en "Nueva Venta" para comenzar.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Color(0xFF64748B)),
                ),
              )
            else
              ...state.sales.reversed.take(5).map((sale) {
                return Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 8),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                    side: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  color: Colors.white,
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFFEFF6FF),
                      child: Icon(
                        sale.esFiada ? Icons.credit_card_off_rounded : Icons.receipt_long_rounded,
                        color: sale.esFiada ? Colors.orange.shade700 : const Color(0xFF2563EB),
                        size: 20,
                      ),
                    ),
                    title: Text(
                      'Factura #${sale.numeroFactura}',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    subtitle: Text(
                      '${sale.metodoPago.toUpperCase()} · ${sale.fecha.split('T').first}',
                      style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          'Bs ${currencyFormat.format(sale.totalBs)}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1E293B)),
                        ),
                        Text(
                          '\$${currencyFormat.format(sale.totalUsd)}',
                          style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                        ),
                      ],
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildKpiCard({
    required String title,
    required String mainValue,
    required String subValue,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(5),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF64748B)),
              ),
              Icon(icon, size: 18, color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            mainValue,
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: color),
          ),
          const SizedBox(height: 2),
          Text(
            subValue,
            style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  void _showQuickRateDialog(BuildContext context, AppState state) {
    final controller = TextEditingController(text: state.exchangeRate.toStringAsFixed(2));
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.currency_exchange_rounded, color: Color(0xFF2563EB)),
            SizedBox(width: 10),
            Text('Tasa Oficial USD / Bs', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ingresa el nuevo valor del dólar en Bolívares. Se actualizará en la PC y en el teléfono al instante.',
              style: TextStyle(fontSize: 13, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: controller,
              autofocus: true,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                labelText: 'Nueva Tasa (Bs / USD)',
                hintText: 'Ej: 763.50',
                prefixIcon: const Icon(Icons.attach_money_rounded),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () {
              final newRate = double.tryParse(controller.text.replaceAll(',', '.'));
              if (newRate != null && newRate > 0) {
                state.setExchangeRate(newRate);
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('✅ Tasa cambiada a Bs ${newRate.toStringAsFixed(2)}. Sincronizando con PC...'),
                    backgroundColor: const Color(0xFF16A34A),
                  ),
                );
              }
            },
            style: FilledButton.styleFrom(backgroundColor: const Color(0xFF2563EB)),
            child: const Text('Guardar y Sincronizar'),
          ),
        ],
      ),
    );
  }
}
