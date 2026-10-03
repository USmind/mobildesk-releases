import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../widgets/sale_detail.dart';
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
  final _ventasSearchController = TextEditingController();
  final Set<String> _expandedFacturas = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _cobrarSearchController.dispose();
    _ventasSearchController.dispose();
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
                // El saldo se revalora con la tasa vigente; mostrar el USD evita
                // que el cliente discuta la cifra ("yo te debo menos dollars").
                Text(
                  'Equivale a \$${(sale.saldoPendienteUsd > 0 ? sale.saldoPendienteUsd : (widget.state.exchangeRate > 0 ? sale.saldoPendiente / widget.state.exchangeRate : 0)).toStringAsFixed(2)}'
                  ' · Tasa Bs ${_currencyFormat.format(widget.state.exchangeRate)}',
                  style: DesignTokens.style('bodySmall'),
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

                widget.state.recordDebtPayment(sale.numeroFactura, amount, metodo: metodo, montoUsd: montoUsd);
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
    // Usa el dialogo compartido: el mismo que se abre desde el inicio.
    // Antes habia una copia separada aqui; cualquier cambio habia que
    // hacerlo en dos sitios y se desincronizaban.
    showSaleDetailDialog(context, widget.state, sale);
  }

  /// Saldo pendiente en USD de una venta. El Bs es derivado, el USD es la verdad.
  double _saldoUsdDe(Sale s) {
    if (s.saldoPendienteUsd > 0) return s.saldoPendienteUsd;
    if (widget.state.exchangeRate > 0) return s.saldoPendiente / widget.state.exchangeRate;
    return 0;
  }

  /// Tarjeta de indicador, con el mismo formato que los KPI de la PC.
  Widget _kpiCard(String titulo, String valor, String detalle) {
    return Container(
      padding: DesignTokens.paddingAll('sm'),
      decoration: BoxDecoration(
        color: DesignTokens.surfaceVariant,
        borderRadius: DesignTokens.borderRadius('md'),
        border: Border.all(color: DesignTokens.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            titulo,
            style: DesignTokens.style('labelSmall').copyWith(
              color: DesignTokens.textMuted,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            valor,
            style: DesignTokens.style('titleSmall').copyWith(
              fontWeight: FontWeight.bold,
              color: DesignTokens.warning,
            ),
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            detalle,
            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
            overflow: TextOverflow.ellipsis,
          ),
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
                  widget.state.recordDebtPayment(sale.numeroFactura, abono, metodo: metodo, montoUsd: abonoUsd);
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
    // Igual que la PC: el buscador también acepta el número de factura.
    final names = grouped.keys
        .where((n) {
          if (query.isEmpty) return true;
          if (n.toLowerCase().contains(query)) return true;
          return grouped[n]!.any((f) => f.numeroFactura.toLowerCase().contains(query));
        })
        .toList()
      ..sort((a, b) {
        // Los que deben más van primero, igual que la PC.
        final sa = grouped[a]!.fold<double>(0, (s, f) => s + f.saldoPendiente);
        final sb = grouped[b]!.fold<double>(0, (s, f) => s + f.saldoPendiente);
        return sb.compareTo(sa);
      });

    if (grouped.isEmpty) {
      return const EmptyState(
        icon: Icons.credit_card_off_outlined,
        title: 'Sin deudas pendientes',
        message: 'Todas las ventas fiadas están saldadas',
      );
    }

    // KPIs con la tasa vigente, como los de la ventana Fiados de la PC.
    final totalPendienteBs = grouped.values
        .expand((l) => l)
        .fold<double>(0, (s, f) => s + f.saldoPendiente);
    final totalPendienteUsd = grouped.values
        .expand((l) => l)
        .fold<double>(0, (s, f) => s + _saldoUsdDe(f));
    final numClientes = grouped.length;

    return Column(
      children: [
        Padding(
          padding: DesignTokens.paddingAll('md'),
          child: Row(
            children: [
              Expanded(
                child: _kpiCard(
                  'POR COBRAR',
                  'Bs ${_currencyFormat.format(totalPendienteBs)}',
                  '\$${_currencyFormat.format(totalPendienteUsd)} · $numClientes cliente(s)',
                ),
              ),
              DesignTokens.spaceSm.width,
              Expanded(
                child: _kpiCard(
                  'TASA APLICADA',
                  'Bs ${_currencyFormat.format(widget.state.exchangeRate)}',
                  '1 USD = Bs ${_currencyFormat.format(widget.state.exchangeRate)}',
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: DesignTokens.paddingSymmetric(h: 'md'),
          child: TextField(
            controller: _cobrarSearchController,
            onChanged: (_) => setState(() {}),
            decoration: InputDecoration(
              hintText: 'Buscar por cliente o número de factura...',
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
                              final fExpanded = _expandedFacturas.contains(f.numeroFactura);
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
                                              _expandedFacturas.remove(f.numeroFactura);
                                            } else {
                                              _expandedFacturas.add(f.numeroFactura);
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
    final pendingCount = widget.state.sales.where((s) => s.esFiada && s.saldoPendiente > 0).length;

    // El buscador del historial filtra por numero de factura o nombre de cliente.
    final queryVentas = _ventasSearchController.text.trim().toLowerCase();
    final ventasFiltradas = queryVentas.isEmpty
        ? widget.state.sales.reversed.toList()
        : widget.state.sales.reversed.where((s) {
            return s.numeroFactura.toLowerCase().contains(queryVentas) ||
                (s.clienteNombre ?? '').toLowerCase().contains(queryVentas);
          }).toList();

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
              : Column(
                  children: [
                    Padding(
                      padding: DesignTokens.paddingAll('md'),
                      child: TextField(
                        controller: _ventasSearchController,
                        onChanged: (_) => setState(() {}),
                        decoration: InputDecoration(
                          hintText: 'Buscar por factura o cliente...',
                          prefixIcon: Icon(Icons.search_rounded, color: DesignTokens.primary),
                          suffixIcon: _ventasSearchController.text.isNotEmpty
                              ? IconButton(
                                  icon: Icon(Icons.clear, color: DesignTokens.textMuted),
                                  onPressed: () => setState(() => _ventasSearchController.clear()),
                                )
                              : null,
                          border: OutlineInputBorder(borderRadius: DesignTokens.borderRadius('md')),
                          filled: true,
                          fillColor: DesignTokens.surfaceVariant,
                        ),
                      ),
                    ),
                    Expanded(
                      child: ventasFiltradas.isEmpty
                          ? EmptyState(
                              icon: Icons.search_off_rounded,
                              title: 'Sin resultados',
                              message: 'No hay ventas que coincidan con "$queryVentas"',
                            )
                          : ListView.builder(
                              padding: DesignTokens.paddingSymmetric(h: 'md'),
                              itemCount: ventasFiltradas.length,
                              itemBuilder: (ctx, i) {
                                final sale = ventasFiltradas[i];
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
                    ),
                  ],
                ),
          // Tab 2: Fiados agrupados por cliente (igual que la PC).
          // Se elimino la pestana "Cobrar" separada: hacia exactamente lo
          // mismo que esta, con el nombre del cliente repetido por factura.
          _buildCobrarTab(),
        ],
      ),
    );
  }
}
