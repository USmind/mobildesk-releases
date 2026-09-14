import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/design_tokens.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../widgets/dialogs.dart';
import '../widgets/states.dart';
import '../utils.dart';

const List<Map<String, String>> kMetodosAbono = [
  {'value': 'efectivo', 'label': 'Efectivo'},
  {'value': 'divisas', 'label': 'Divisas'},
  {'value': 'pago_movil', 'label': 'Pago móvil'},
  {'value': 'tarjeta', 'label': 'Tarjeta'},
];

class SalesHistoryScreen extends StatefulWidget {
  final AppState state;
  final void Function(String clientName)? onFiarMas;
  const SalesHistoryScreen({super.key, required this.state, this.onFiarMas});

  @override
  State<SalesHistoryScreen> createState() => _SalesHistoryScreenState();
}

class _SalesHistoryScreenState extends State<SalesHistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _currencyFormat = NumberFormat('#,##0.00', 'es_VE');
  final _cobrarSearchController = TextEditingController();
  final Set<String> _expandedFacturas = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _cobrarSearchController.dispose();
    super.dispose();
  }

  void _registerDebtPayment(Sale sale) {
    final amountCtrl = TextEditingController();
    final usdCtrl = TextEditingController();
    String metodo = 'efectivo';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
          title: Text('Registrar Pago de Deuda', style: DesignTokens.style('titleLarge')),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Cliente: ${sale.clienteNombre ?? 'Sin nombre'}', style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold)),
                Text('Factura: #${sale.numeroFactura}', style: DesignTokens.style('bodyMedium')),
                Text(
                  'Saldo Pendiente: Bs ${_currencyFormat.format(sale.saldoPendiente)}',
                  style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.error),
                ),
                DesignTokens.spaceMd.height,
                TextField(
                  controller: amountCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Monto recibido en Bs',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: metodo,
                  decoration: InputDecoration(
                    labelText: 'Método de pago',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: kMetodosAbono
                      .map((m) => DropdownMenuItem(value: m['value']!, child: Text(m['label']!)))
                      .toList(),
                  onChanged: (v) => setModalState(() => metodo = v ?? 'efectivo'),
                ),
                if (metodo == 'divisas') ...[
                  DesignTokens.spaceMd.height,
                  TextField(
                    controller: usdCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: 'Monto en USD (opcional)',
                      border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                final amount = double.tryParse(amountCtrl.text.replaceAll(',', '.')) ?? 0;
                if (amount <= 0 || amount > sale.saldoPendiente) {
                  showErrorDialog(context, title: 'Monto inválido', message: 'El monto debe ser mayor a cero y no superar el saldo pendiente.');
                  return;
                }
                final montoUsd = metodo == 'divisas'
                    ? double.tryParse(usdCtrl.text.replaceAll(',', '.'))
                    : null;

                widget.state.recordDebtPayment(sale.id, amount, metodo: metodo, montoUsd: montoUsd);
                Navigator.pop(ctx);
                showSuccessDialog(context, title: 'Registrado', message: 'Pago de deuda registrado correctamente.');
              },
              child: const Text('Guardar Pago'),
            ),
          ],
        ),
      ),
    );
  }

  void _showSaleDetail(Sale sale) {
    final pd = sale.pagosDetalle;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
        title: Text('Factura #${sale.numeroFactura}', style: DesignTokens.style('titleLarge')),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${sale.fecha.split('T').first} · ${sale.metodoPago.toUpperCase()}',
                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
              ),
              if (sale.clienteNombre != null && sale.clienteNombre!.isNotEmpty) ...[
                DesignTokens.spaceXs.height,
                Text('Cliente: ${sale.clienteNombre}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
              ],
              DesignTokens.spaceSm.height,
              Text('Productos (${sale.productos.length})', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
              const Divider(height: 12),
              if (sale.productos.isEmpty)
                Text('Sin detalle de productos.', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted))
              else
                ...sale.productos.map((p) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              softWrap: true,
                              '${p.cantidad.toStringAsFixed(p.cantidad.truncateToDouble() == p.cantidad ? 0 : 2)} x ${p.nombre.isNotEmpty ? p.nombre : p.codigo}',
                              style: DesignTokens.style('bodySmall'),
                            ),
                          ),
                          Text(
                            'Bs ${_currencyFormat.format(p.cantidad * p.precioUsd * sale.tasa)}',
                            style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    )),
              const Divider(height: 12),
              Text('Total: Bs ${_currencyFormat.format(sale.totalBs)} (\$${_currencyFormat.format(sale.totalUsd)})',
                  style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
              Text('Tasa: Bs ${_currencyFormat.format(sale.tasa)}',
                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
              if (pd != null && sale.metodoPago == 'mixto') ...[
                DesignTokens.spaceXs.height,
                if (pd.divisasUsd > 0)
                  Text('  • Divisas: \$${_currencyFormat.format(pd.divisasUsd)}', style: DesignTokens.style('bodySmall')),
                if (pd.efectivoBs > 0)
                  Text('  • Efectivo: Bs ${_currencyFormat.format(pd.efectivoBs)}', style: DesignTokens.style('bodySmall')),
                if (pd.pagoMovilBs > 0)
                  Text('  • Pago Móvil: Bs ${_currencyFormat.format(pd.pagoMovilBs)}', style: DesignTokens.style('bodySmall')),
                if (pd.tarjetaBs > 0)
                  Text('  • Tarjeta: Bs ${_currencyFormat.format(pd.tarjetaBs)}', style: DesignTokens.style('bodySmall')),
                if (pd.fiadoBs > 0)
                  Text('  • Fiado: Bs ${_currencyFormat.format(pd.fiadoBs)}', style: DesignTokens.style('bodySmall')),
              ],
              if (sale.esFiada) ...[
                DesignTokens.spaceXs.height,
                Text('Saldo pendiente: Bs ${_currencyFormat.format(sale.saldoPendiente)}',
                    style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.warning)),
              ],
              if (sale.vueltoBs > 0)
                Text('Vuelto: Bs ${_currencyFormat.format(sale.vueltoBs)}',
                    style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.success)),
              if (sale.vueltoUsd > 0)
                Text('Vuelto: \$${_currencyFormat.format(sale.vueltoUsd)}',
                    style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.success)),
            ],
          ),
        ),
        actions: [
          FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cerrar')),
        ],
      ),
    );
  }

  Map<String, List<Sale>> _groupDebtsByClient() {
    final debts = widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0).toList();
    final map = <String, List<Sale>>{};
    for (final s in debts) {
      final key = (s.clienteNombre ?? 'Sin nombre').trim();
      final name = key.isEmpty ? 'Sin nombre' : key;
      map.putIfAbsent(name, () => []).add(s);
    }
    for (final list in map.values) {
      list.sort((a, b) => a.fecha.compareTo(b.fecha));
    }
    return map;
  }

  void _showCobrarDialog(String clientName, List<Sale> facturas, double totalDeuda) {
    final amountCtrl = TextEditingController(text: totalDeuda.toStringAsFixed(2));
    final usdCtrl = TextEditingController();
    String metodo = 'efectivo';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('lg')),
          title: Text('Cobrar a $clientName', style: DesignTokens.style('titleLarge')),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Deuda total: Bs ${_currencyFormat.format(totalDeuda)} (${facturas.length} factura(s), más vieja primero)',
                  style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold),
                ),
                DesignTokens.spaceMd.height,
                TextField(
                  controller: amountCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Monto del abono en Bs',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                ),
                DesignTokens.spaceMd.height,
                DropdownButtonFormField<String>(
                  value: metodo,
                  decoration: InputDecoration(
                    labelText: 'Método de pago',
                    border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                  ),
                  items: kMetodosAbono
                      .map((m) => DropdownMenuItem(value: m['value']!, child: Text(m['label']!)))
                      .toList(),
                  onChanged: (v) => setModalState(() => metodo = v ?? 'efectivo'),
                ),
                if (metodo == 'divisas') ...[
                  DesignTokens.spaceMd.height,
                  TextField(
                    controller: usdCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: 'Monto en USD (opcional)',
                      border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                    ),
                  ),
                ],
                DesignTokens.spaceSm.height,
                Text(
                  'El abono se reparte automáticamente a las facturas más viejas.',
                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                final amount = double.tryParse(amountCtrl.text.replaceAll(',', '.')) ?? 0;
                if (amount <= 0 || amount > totalDeuda) {
                  showErrorDialog(context, title: 'Monto inválido', message: 'El monto debe ser mayor a cero y no superar la deuda total (Bs ${_currencyFormat.format(totalDeuda)}).');
                  return;
                }
                final totalUsd = metodo == 'divisas'
                    ? double.tryParse(usdCtrl.text.replaceAll(',', '.'))
                    : null;

                double restante = amount;
                int afectadas = 0;
                for (final sale in facturas) {
                  if (restante <= 0) break;
                  if (sale.saldoPendiente <= 0) continue;
                  final abono = restante >= sale.saldoPendiente ? sale.saldoPendiente : restante;
                  double? abonoUsd;
                  if (totalUsd != null && totalUsd > 0 && amount > 0) {
                    abonoUsd = abono * totalUsd / amount;
                  }
                  widget.state.recordDebtPayment(sale.id, abono, metodo: metodo, montoUsd: abonoUsd);
                  restante -= abono;
                  afectadas++;
                }
                Navigator.pop(ctx);
                showSuccessDialog(context, title: 'Cobro registrado', message: 'Abono de Bs ${_currencyFormat.format(amount)} repartido en $afectadas factura(s) de $clientName.');
              },
              child: const Text('Cobrar'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCobrarTab() {
    final query = _cobrarSearchController.text.trim().toLowerCase();
    final grouped = _groupDebtsByClient();
    final names = grouped.keys
        .where((n) => query.isEmpty || n.toLowerCase().contains(query))
        .toList()
      ..sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));

    if (grouped.isEmpty) {
      return const EmptyState(
        icon: Icons.credit_card_off_outlined,
        title: 'Sin deudas pendientes',
        message: 'Todas las ventas fiadas están saldadas',
      );
    }

    return Column(
      children: [
        Padding(
          padding: DesignTokens.paddingAll('md'),
          child: TextField(
            controller: _cobrarSearchController,
            onChanged: (_) => setState(() {}),
            decoration: InputDecoration(
              hintText: 'Buscar por nombre de cliente...',
              prefixIcon: Icon(Icons.search_rounded, color: DesignTokens.primary),
              suffixIcon: _cobrarSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: Icon(Icons.clear, color: DesignTokens.textMuted),
                      onPressed: () => setState(() => _cobrarSearchController.clear()),
                    )
                  : null,
              border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
              filled: true,
              fillColor: DesignTokens.surfaceVariant,
            ),
          ),
        ),
        Expanded(
          child: names.isEmpty
              ? EmptyState(
                  icon: Icons.person_search_outlined,
                  title: 'Sin resultados',
                  message: 'No hay clientes con "$query"',
                )
              : ListView.builder(
                  padding: DesignTokens.paddingSymmetric(h: 'md'),
                  itemCount: names.length,
                  itemBuilder: (ctx, i) {
                    final name = names[i];
                    final facturas = grouped[name]!;
                    final total = facturas.fold<double>(0, (s, f) => s + f.saldoPendiente);
                    return Card(
                      elevation: 0,
                      margin: DesignTokens.paddingOnly(bottom: 'sm'),
                      shape: RoundedRectangleBorder(
                        borderRadius: DesignTokens.borderRadius('lg'),
                        side: BorderSide(color: DesignTokens.warningLight, width: 1.5),
                      ),
                      color: DesignTokens.surface,
                      child: Padding(
                        padding: DesignTokens.paddingAll('md'),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(name, softWrap: true, style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold)),
                                      Text(
                                        softWrap: true,
                                        '${facturas.length} factura(s) · Deuda total: Bs ${_currencyFormat.format(total)}',
                                        style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.warning),
                                      ),
                                    ],
                                  ),
                                ),
                                DesignTokens.spaceSm.width,
                                FilledButton(
                                  style: FilledButton.styleFrom(
                                    backgroundColor: DesignTokens.success,
                                    padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                                    minimumSize: const Size(0, 36),
                                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                  ),
                                  onPressed: () => _showCobrarDialog(name, facturas, total),
                                  child: Text('Cobrar', style: DesignTokens.style('labelMedium').copyWith(color: Colors.white)),
                                ),
                                DesignTokens.spaceSm.width,
                                OutlinedButton(
                                  style: OutlinedButton.styleFrom(
                                    padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                                    minimumSize: const Size(0, 36),
                                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                    visualDensity: VisualDensity.compact,
                                  ),
                                  onPressed: widget.onFiarMas == null ? null : () => widget.onFiarMas!(name),
                                  child: Text('Agregar', style: DesignTokens.style('labelMedium')),
                                ),
                              ],
                            ),
                            DesignTokens.spaceSm.height,
                            ...facturas.map((f) {
                              final fExpanded = _expandedFacturas.contains(f.id);
                              return Padding(
                                padding: const EdgeInsets.only(bottom: 4),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      crossAxisAlignment: CrossAxisAlignment.center,
                                      children: [
                                        Expanded(
                                          child: Text(
                                            softWrap: true,
                                            '#${f.numeroFactura} · ${f.fecha.split('T').first} · Saldo Bs ${_currencyFormat.format(f.saldoPendiente)}',
                                            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textSecondary),
                                          ),
                                        ),
                                        TextButton(
                                          style: TextButton.styleFrom(
                                            minimumSize: const Size(0, 32),
                                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                            visualDensity: VisualDensity.compact,
                                          ),
                                          onPressed: () => setState(() {
                                            if (fExpanded) {
                                              _expandedFacturas.remove(f.id);
                                            } else {
                                              _expandedFacturas.add(f.id);
                                            }
                                          }),
                                          child: Text(fExpanded ? 'Ocultar' : 'Productos'),
                                        ),
                                        TextButton(
                                          style: TextButton.styleFrom(
                                            minimumSize: const Size(0, 32),
                                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                            visualDensity: VisualDensity.compact,
                                          ),
                                          onPressed: () => _registerDebtPayment(f),
                                          child: const Text('Abonar'),
                                        ),
                                      ],
                                    ),
                                    if (fExpanded)
                                      Padding(
                                        padding: const EdgeInsets.only(left: 8, top: 2, bottom: 6),
                                        child: f.productos.isEmpty
                                            ? Text(
                                                'Sin detalle de productos.',
                                                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                              )
                                            : Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: f.productos
                                                    .map((p) => Text(
                                                          softWrap: true,
                                                          '• ${p.cantidad.toStringAsFixed(p.cantidad.truncateToDouble() == p.cantidad ? 0 : 2)} x ${p.nombre.isNotEmpty ? p.nombre : p.codigo} — Bs ${_currencyFormat.format(p.cantidad * p.precioUsd * f.tasa)}',
                                                          style: DesignTokens.style('bodySmall'),
                                                        ))
                                                    .toList(),
                                              ),
                                      ),
                                  ],
                                ),
                              );
                            }),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final creditSales = widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0).toList().reversed.toList();
    final pendingCount = widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0).length;

    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Historial de Ventas', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: DesignTokens.textOnPrimary,
          unselectedLabelColor: DesignTokens.primaryLight,
          indicatorColor: DesignTokens.textOnPrimary,
          tabs: [
            Tab(text: 'Ventas (${widget.state.sales.length})'),
            Tab(text: 'Fiados ($pendingCount)'),
            const Tab(text: 'Cobrar'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Todas las ventas
          widget.state.sales.isEmpty
              ? const EmptyState(
                  icon: Icons.receipt_long_outlined,
                  title: 'Sin ventas registradas',
                  message: 'Las ventas aparecerán aquí al registrar desde el POS',
                )
              : ListView.builder(
                  padding: DesignTokens.paddingAll('md'),
                  itemCount: widget.state.sales.reversed.toList().length,
                  itemBuilder: (ctx, i) {
                    final sale = widget.state.sales.reversed.toList()[i];
                    return Card(
                      elevation: 0,
                      margin: DesignTokens.paddingOnly(bottom: 'sm'),
                      shape: RoundedRectangleBorder(
                        borderRadius: DesignTokens.borderRadius('lg'),
                        side: BorderSide(color: DesignTokens.border),
                      ),
                      color: DesignTokens.surface,
                      child: ListTile(
                        onTap: () => _showSaleDetail(sale),
                        title: Text('Factura #${sale.numeroFactura}', style: DesignTokens.style('bodyLarge').copyWith(fontWeight: FontWeight.bold)),
                        subtitle: Text(
                          '${sale.fecha.split('T').first} · ${sale.metodoPago.toUpperCase()}'
                          '${sale.clienteNombre != null ? ' · Cliente: ${sale.clienteNombre}' : ''}',
                          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              'Bs ${_currencyFormat.format(sale.totalBs)}',
                              style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.text),
                            ),
                            Text(
                              '\$${_currencyFormat.format(sale.totalUsd)}',
                              style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
          // Tab 2: Fiados (individual por factura, se conserva)
          creditSales.isEmpty
              ? const EmptyState(
                  icon: Icons.credit_card_off_outlined,
                  title: 'Sin deudas pendientes',
                  message: 'Todas las ventas fiadas están saldadas',
                )
              : ListView.builder(
                  padding: DesignTokens.paddingAll('md'),
                  itemCount: creditSales.length,
                  itemBuilder: (ctx, i) {
                    final sale = creditSales[i];
                    final expanded = _expandedFacturas.contains(sale.id);
                    return Card(
                      elevation: 0,
                      margin: DesignTokens.paddingOnly(bottom: 'sm'),
                      shape: RoundedRectangleBorder(
                        borderRadius: DesignTokens.borderRadius('lg'),
                        side: BorderSide(color: DesignTokens.warningLight, width: 1.5),
                      ),
                      color: DesignTokens.surface,
                      child: Padding(
                        padding: DesignTokens.paddingAll('md'),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        sale.clienteNombre ?? 'Cliente',
                                        softWrap: true,
                                        style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold),
                                      ),
                                      DesignTokens.spaceXs.height,
                                      Text(
                                        softWrap: true,
                                        'Factura #${sale.numeroFactura} · Total: Bs ${_currencyFormat.format(sale.totalBs)}',
                                        style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                      ),
                                      DesignTokens.spaceXs.height,
                                      Text(
                                        softWrap: true,
                                        'Saldo Pendiente: Bs ${_currencyFormat.format(sale.saldoPendiente)}',
                                        style: DesignTokens.style('bodyMedium').copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: DesignTokens.warning,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                DesignTokens.spaceSm.width,
                                Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    FilledButton(
                                      style: FilledButton.styleFrom(
                                        backgroundColor: DesignTokens.secondary,
                                        padding: DesignTokens.paddingSymmetric(h: 'md', v: 'sm'),
                                        minimumSize: const Size(0, 36),
                                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                      ),
                                      onPressed: () => _registerDebtPayment(sale),
                                      child: Text('Abonar', style: DesignTokens.style('labelMedium').copyWith(color: Colors.white)),
                                    ),
                                    TextButton(
                                      style: TextButton.styleFrom(
                                        minimumSize: const Size(0, 32),
                                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                        visualDensity: VisualDensity.compact,
                                      ),
                                      onPressed: () => setState(() {
                                        if (expanded) {
                                          _expandedFacturas.remove(sale.id);
                                        } else {
                                          _expandedFacturas.add(sale.id);
                                        }
                                      }),
                                      child: Text(expanded ? 'Ocultar productos' : 'Ver productos (${sale.productos.length})'),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            if (expanded) ...[
                              DesignTokens.spaceSm.height,
                              const Divider(height: 12),
                              if (sale.productos.isEmpty)
                                Text(
                                  'Sin detalle de productos para esta factura.',
                                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                                )
                              else
                                ...sale.productos.map((p) => Padding(
                                      padding: const EdgeInsets.only(bottom: 4),
                                      child: Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              '${p.cantidad.toStringAsFixed(p.cantidad.truncateToDouble() == p.cantidad ? 0 : 2)} x ${p.nombre.isNotEmpty ? p.nombre : p.codigo}',
                                              softWrap: true,
                                              style: DesignTokens.style('bodySmall'),
                                            ),
                                          ),
                                          Text(
                                            'Bs ${_currencyFormat.format(p.cantidad * p.precioUsd * sale.tasa)}',
                                            style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold),
                                          ),
                                        ],
                                      ),
                                    )),
                              Align(
                                alignment: Alignment.centerRight,
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.add_rounded, size: 18),
                                  label: const Text('Agregar a su cuenta'),
                                  onPressed: widget.onFiarMas == null || sale.clienteNombre == null
                                      ? null
                                      : () => widget.onFiarMas!(sale.clienteNombre!),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
          // Tab 3: Cobrar (agrupado por cliente)
          _buildCobrarTab(),
        ],
      ),
    );
  }
}
