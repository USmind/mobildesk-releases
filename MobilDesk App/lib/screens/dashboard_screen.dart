import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/design_tokens.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';
import '../widgets/states.dart';
import '../utils.dart';

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

    // Sync status colors
    final isSynced = state.syncStatus.contains('Sincronizado');
    final isError = state.syncStatus.contains('Error') ||
        state.syncStatus.contains('vencida') ||
        state.syncStatus.contains('Sin conexión');

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              state.businessName.toUpperCase(),
              style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5, color: DesignTokens.textOnPrimary),
            ),
            Text(
              'Panel de Control',
              style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.primaryLight),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Actualizar tasa BCV',
            icon: Icon(Icons.currency_exchange_rounded, color: DesignTokens.textOnPrimary),
            onPressed: () async {
              final oldRate = state.exchangeRate;
              await state.fetchBcvRateAndUpdate();
              if (context.mounted) {
                final msg = state.exchangeRate != oldRate
                    ? 'Tasa BCV actualizada: 1 USD = Bs ${state.exchangeRate.toStringAsFixed(2)}'
                    : 'Tasa BCV sin cambios: 1 USD = Bs ${state.exchangeRate.toStringAsFixed(2)}';
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
              }
            },
          ),
          IconButton(
            tooltip: 'Sincronizar',
            icon: state.isSyncing
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: DesignTokens.textOnPrimary),
                  )
                : Icon(Icons.sync_rounded, color: DesignTokens.textOnPrimary),
            onPressed: state.isSyncing ? null : state.sync,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: state.sync,
        color: DesignTokens.primary,
        child: ListView(
          padding: DesignTokens.paddingAll('lg'),
          children: [
            // Status Banner
            InkWell(
              onTap: state.isSyncing ? null : state.sync,
              borderRadius: DesignTokens.borderRadius('md'),
              child: Container(
                padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                decoration: BoxDecoration(
                  color: state.syncStatus.contains('Sincronizado')
                      ? DesignTokens.successContainer
                      : (state.syncStatus.contains('Error') ||
                              state.syncStatus.contains('vencida') ||
                              state.syncStatus.contains('Sin conexión'))
                          ? DesignTokens.errorContainer
                          : DesignTokens.primaryContainer,
                  borderRadius: DesignTokens.borderRadius('md'),
                  border: Border.all(
                    color: state.syncStatus.contains('Sincronizado')
                        ? DesignTokens.successLight
                        : (state.syncStatus.contains('Error') ||
                                state.syncStatus.contains('vencida') ||
                                state.syncStatus.contains('Sin conexión'))
                            ? DesignTokens.errorLight
                            : DesignTokens.primaryLight,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      state.syncStatus.contains('Sincronizado')
                          ? Icons.cloud_done_rounded
                          : (state.syncStatus.contains('Error') ||
                                  state.syncStatus.contains('vencida') ||
                                  state.syncStatus.contains('Sin conexión'))
                              ? Icons.cloud_off_rounded
                              : Icons.sync_rounded,
                      size: 20,
                      color: state.syncStatus.contains('Sincronizado')
                          ? DesignTokens.success
                          : (state.syncStatus.contains('Error') ||
                                  state.syncStatus.contains('vencida') ||
                                  state.syncStatus.contains('Sin conexión'))
                              ? DesignTokens.error
                              : DesignTokens.primary,
                    ),
                    DesignTokens.spaceSm.width,
                    Expanded(
                      child: Text(
                        state.syncStatus,
                        style: DesignTokens.style('labelLarge').copyWith(
                          color: state.syncStatus.contains('Sincronizado')
                              ? DesignTokens.success
                              : (state.syncStatus.contains('Error') ||
                                      state.syncStatus.contains('vencida') ||
                                      state.syncStatus.contains('Sin conexión'))
                                  ? DesignTokens.error
                                  : DesignTokens.primaryDark,
                        ),
                      ),
                    ),
                    if (state.outbox.isNotEmpty)
                      Container(
                        padding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
                        decoration: BoxDecoration(
                          color: DesignTokens.warningLight,
                          borderRadius: DesignTokens.borderRadius('full'),
                        ),
                        child: Text(
                          '${state.outbox.length} pendientes',
                          style: DesignTokens.style('labelSmall').copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            DesignTokens.spaceMd.height,

            // Tasa USD/Bs Banner
            Card(
              elevation: 0,
              color: DesignTokens.primaryDark,
              shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
              child: InkWell(
                onTap: () => _showQuickRateDialog(context, state),
                borderRadius: DesignTokens.borderRadius('lg'),
                child: Padding(
                  padding: DesignTokens.paddingAll('md'),
                  child: Row(
                    children: [
                      Icon(Icons.currency_exchange_rounded, color: DesignTokens.textOnPrimary, size: 28),
                      DesignTokens.spaceMd.width,
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  'TASA OFICIAL USD / BS',
                                  style: DesignTokens.style('labelSmall').copyWith(
                                    color: DesignTokens.primaryLight,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                DesignTokens.spaceXs.width,
                                Icon(Icons.edit_rounded, color: DesignTokens.primaryLight, size: 12),
                              ],
                            ),
                            Text(
                              '1 USD = Bs ${currencyFormat.format(state.exchangeRate)}',
                              style: DesignTokens.style('headlineSmall').copyWith(
                                color: DesignTokens.textOnPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (state.lastBcvUpdate != null && state.lastBcvUpdate!.isNotEmpty)
                              Text(
                                'BCV: ${state.lastBcvUpdate}',
                                style: DesignTokens.style('labelSmall').copyWith(
                                  color: DesignTokens.primaryLight,
                                ),
                              ),
                          ],
                        ),
                      ),
                      if (state.profitMargin > 0)
                        Container(
                          padding: DesignTokens.paddingSymmetric(h: 'sm', v: 'xs'),
                          decoration: BoxDecoration(
                            color: DesignTokens.primary,
                            borderRadius: DesignTokens.borderRadius('sm'),
                          ),
                          child: Text(
                            '+${state.profitMargin.toStringAsFixed(0)}% ganancia',
                            style: DesignTokens.style('labelSmall').copyWith(
                              color: DesignTokens.textOnPrimary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
            DesignTokens.spaceMd.height,

            // KPIs Grid
            Row(
              children: [
                Expanded(
                  child: _buildKpiCard(
                    title: 'VENTAS HOY',
                    mainValue: 'Bs ${currencyFormat.format(totalBsToday)}',
                    subValue: '\$${currencyFormat.format(totalUsdToday)} (${salesToday.length} ventas)',
                    color: DesignTokens.primary,
                    icon: Icons.point_of_sale_rounded,
                  ),
                ),
                DesignTokens.spaceMd.width,
                Expanded(
                  child: _buildKpiCard(
                    title: 'PRODUCTOS',
                    mainValue: '${activeProducts.length}',
                    subValue: 'Catálogo Activo',
                    color: DesignTokens.success,
                    icon: Icons.inventory_2_rounded,
                  ),
                ),
              ],
            ),
            DesignTokens.spaceLg.height,

            // Quick Action Shortcuts
            Text(
              'Acciones Rápidas',
              style: DesignTokens.style('titleMedium').copyWith(
                fontWeight: FontWeight.bold,
                color: DesignTokens.text,
              ),
            ),
            DesignTokens.spaceMd.height,
            Row(
              children: [
                Expanded(
                  child: _buildActionButton(
                    icon: Icons.add_shopping_cart_rounded,
                    label: 'Nueva Venta',
                    color: DesignTokens.primary,
                    onTap: () => onNavigateTab(1),
                  ),
                ),
                DesignTokens.spaceMd.width,
                Expanded(
                  child: _buildActionButton(
                    icon: Icons.add_box_rounded,
                    label: 'Inventario',
                    color: DesignTokens.secondary,
                    onTap: () => onNavigateTab(3),
                  ),
                ),
              ],
            ),
            DesignTokens.spaceXl.height,

            // Recent sales list
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Últimas Ventas Registradas',
                  style: DesignTokens.style('titleMedium').copyWith(
                    fontWeight: FontWeight.bold,
                    color: DesignTokens.text,
                  ),
                ),
                TextButton(
                  onPressed: () => onNavigateTab(4),
                  child: Text('Ver todas', style: DesignTokens.style('labelLarge').copyWith(color: DesignTokens.primary)),
                ),
              ],
            ),
            DesignTokens.spaceMd.height,
            state.sales.isEmpty
                ? EmptyState(
                    icon: Icons.receipt_long_outlined,
                    title: 'Sin ventas registradas',
                    message: 'Pulsa en "Nueva Venta" para comenzar',
                    actionLabel: 'Nueva Venta',
                    onAction: () => onNavigateTab(1),
                  )
                : ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: state.sales.reversed.take(5).length,
                    separatorBuilder: (_, __) => DesignTokens.spaceSm.height,
                    itemBuilder: (ctx, i) {
                      final salesList = state.sales.reversed.take(5).toList();
                      final sale = salesList[i];
                      return Card(
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: DesignTokens.borderRadius('lg'),
                          side: BorderSide(color: DesignTokens.border),
                        ),
                        color: DesignTokens.surface,
                        child: ListTile(
                          contentPadding: DesignTokens.paddingSymmetric(h: 'md', v: 'xs'),
                          leading: CircleAvatar(
                            backgroundColor: sale.esFiada ? DesignTokens.warningContainer : DesignTokens.primaryContainer,
                            child: Icon(
                              sale.esFiada ? Icons.credit_card_off_rounded : Icons.receipt_long_rounded,
                              color: sale.esFiada ? DesignTokens.warning : DesignTokens.primary,
                              size: 20,
                            ),
                          ),
                          title: Text(
                            'Factura #${sale.numeroFactura}',
                            style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text(
                            '${sale.metodoPago.toUpperCase()} · ${sale.fecha.split('T').first}',
                            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                'Bs ${currencyFormat.format(sale.totalBs)}',
                                style: DesignTokens.style('titleMedium').copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: DesignTokens.text,
                                ),
                              ),
                              Text(
                                '\$${currencyFormat.format(sale.totalUsd)}',
                                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
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
      padding: DesignTokens.paddingAll('md'),
      decoration: BoxDecoration(
        color: DesignTokens.surface,
        borderRadius: DesignTokens.borderRadius('lg'),
        border: Border.all(color: DesignTokens.border),
        boxShadow: DesignTokens.elevation1,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: DesignTokens.style('labelSmall').copyWith(
                fontWeight: FontWeight.bold,
                color: DesignTokens.textMuted,
              )),
              Icon(icon, size: 18, color: color),
            ],
          ),
          DesignTokens.spaceMd.height,
          Text(mainValue, style: DesignTokens.style('headlineSmall').copyWith(
            fontWeight: FontWeight.bold,
            color: color,
          )),
          DesignTokens.spaceXs.height,
          Text(subValue, style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
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
      borderRadius: DesignTokens.borderRadius('md'),
      child: Container(
        padding: DesignTokens.paddingSymmetric(v: 'md', h: 'lg'),
        decoration: BoxDecoration(
          color: color,
          borderRadius: DesignTokens.borderRadius('md'),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: DesignTokens.textOnPrimary, size: 20),
            DesignTokens.spaceSm.width,
            Text(
              label,
              style: DesignTokens.style('labelLarge').copyWith(
                color: DesignTokens.textOnPrimary,
                fontWeight: FontWeight.bold,
              ),
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
        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
        title: Row(
          children: [
            Icon(Icons.currency_exchange_rounded, color: DesignTokens.primary),
            DesignTokens.spaceMd.width,
            Text('Tasa Oficial USD / Bs', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ingresa el nuevo valor del dólar en Bolívares. Se actualizará en la PC y en el teléfono al instante.',
              style: DesignTokens.style('bodyMedium').copyWith(color: DesignTokens.textMuted),
            ),
            DesignTokens.spaceLg.height,
            TextField(
              controller: controller,
              autofocus: true,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              style: DesignTokens.style('headlineSmall').copyWith(fontWeight: FontWeight.bold),
              decoration: InputDecoration(
                labelText: 'Nueva Tasa (Bs / USD)',
                hintText: 'Ej: 763.50',
                prefixIcon: Icon(Icons.attach_money_rounded, color: DesignTokens.primary),
                border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
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
                showSuccessDialog(context, title: 'Actualizado', message: 'Tasa cambiada a Bs ${newRate.toStringAsFixed(2)}. Sincronizando con PC...');
              }
            },
            style: FilledButton.styleFrom(backgroundColor: DesignTokens.primary),
            child: const Text('Guardar y Sincronizar'),
          ),
        ],
      ),
    );
  }
}