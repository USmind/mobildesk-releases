import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/design_tokens.dart';
import '../widgets/states.dart';

/// Reportes financieros de la App.
///
/// Replica los KPI de la ventana 'Reportes' de la PC para que ambos lados
/// muestren las mismas cifras: total de ventas, ticket promedio, ganancia
/// estimada, deudas pendientes, productos mas vendidos y stock critico.
///
/// Los saldos en Bs se derivan del USD con la tasa vigente, igual que en la PC.
class ReportsScreen extends StatefulWidget {
  final AppState state;
  const ReportsScreen({super.key, required this.state});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _fmt = NumberFormat('#,##0.00', 'es_VE');

  /// Periodo seleccionado: 0 = hoy, 1 = semana, 2 = mes, 3 = todo.
  int _periodo = 2;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  /// Ventana de fechas segun el periodo elegido.
  DateTime? get _desde {
    final now = DateTime.now();
    switch (_periodo) {
      case 0:
        return DateTime(now.year, now.month, now.day);
      case 1:
        return now.subtract(const Duration(days: 7));
      case 2:
        return DateTime(now.year, now.month, 1);
      default:
        return null;
    }
  }

  List<Sale> get _ventas {
    final desde = _desde;
    if (desde == null) return widget.state.sales;
    return widget.state.sales.where((s) {
      final f = DateTime.tryParse(s.fecha);
      return f != null && f.isAfter(desde.subtract(const Duration(seconds: 1)));
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Reportes', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: DesignTokens.textOnPrimary,
          unselectedLabelColor: DesignTokens.primaryLight,
          indicatorColor: DesignTokens.textOnPrimary,
          tabs: const [
            Tab(text: 'Resumen'),
            Tab(text: 'Productos'),
            Tab(text: 'Stock'),
          ],
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: DesignTokens.paddingAll('md'),
            child: Row(
              children: [
                for (final p in [
                  ('Hoy', 0),
                  ('7 días', 1),
                  ('Este mes', 2),
                  ('Todo', 3),
                ]) ...[
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: _periodoChip(p.$1, p.$2),
                    ),
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildResumen(),
                _buildProductos(),
                _buildStock(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _periodoChip(String etiqueta, int valor) {
    final activo = _periodo == valor;
    return Material(
      color: activo ? DesignTokens.primaryContainer : DesignTokens.surfaceVariant,
      borderRadius: DesignTokens.borderRadius('md'),
      child: InkWell(
        borderRadius: DesignTokens.borderRadius('md'),
        onTap: () => setState(() => _periodo = valor),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: DesignTokens.borderRadius('md'),
            border: Border.all(color: activo ? DesignTokens.primary : DesignTokens.border),
          ),
          child: Text(
            etiqueta,
            style: DesignTokens.style('labelSmall').copyWith(
              fontWeight: FontWeight.bold,
              color: activo ? DesignTokens.primaryDark : DesignTokens.textSecondary,
            ),
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------- Resumen
  Widget _buildResumen() {
    final ventas = _ventas;
    final totalBs = ventas.fold<double>(0, (s, v) => s + v.totalBs);
    final totalUsd = ventas.fold<double>(0, (s, v) => s + v.totalUsd);
    final n = ventas.length;
    final ticketBs = n > 0 ? totalBs / n : 0.0;
    final ticketUsd = n > 0 ? totalUsd / n : 0.0;

    // Deudas pendientes: saldo USD x tasa vigente (igual que la PC).
    final tasa = widget.state.exchangeRate;
    final pendientes = widget.state.sales.where((s) => s.esFiada && _saldoUsd(s) > 0).toList();
    final pendienteUsd = pendientes.fold<double>(0, (s, v) => s + _saldoUsd(v));
    final pendienteBs = tasa > 0 ? pendienteUsd * tasa : 0.0;

    // Total por metodo de pago, como en la PC.
    final porMetodo = <String, double>{};
    for (final venta in ventas) {
      porMetodo.update(
        venta.metodoPago,
        (acumulado) => acumulado + venta.totalBs,
        ifAbsent: () => venta.totalBs,
      );
    }

    if (ventas.isEmpty) {
      return const EmptyState(
        icon: Icons.bar_chart_rounded,
        title: 'Sin ventas en el periodo',
        message: 'No hay ventas registradas en el periodo seleccionado',
      );
    }

    return ListView(
      padding: DesignTokens.paddingAll('md'),
      children: [
        Row(
          children: [
            Expanded(child: _kpi('VENTAS TOTALES', 'Bs ${_fmt.format(totalBs)}', '\$${_fmt.format(totalUsd)}')),
            SizedBox(width: DesignTokens.spaceSm),
            Expanded(child: _kpi('TICKET PROMEDIO', 'Bs ${_fmt.format(ticketBs)}', '\$${_fmt.format(ticketUsd)}')),
          ],
        ),
        SizedBox(height: DesignTokens.spaceSm),
        Row(
          children: [
            Expanded(child: _kpi('TRANSACCIONES', '$n', 'ventas del periodo')),
            SizedBox(width: DesignTokens.spaceSm),
            Expanded(
              child: _kpi(
                'POR COBRAR',
                'Bs ${_fmt.format(pendienteBs)}',
                '\$${_fmt.format(pendienteUsd)} · ${pendientes.length} deuda(s)',
                color: DesignTokens.warning,
              ),
            ),
          ],
        ),
        SizedBox(height: DesignTokens.spaceLg),
        Text('Por método de pago', style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold)),
        SizedBox(height: DesignTokens.spaceSm),
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: DesignTokens.borderRadius('lg'),
            side: BorderSide(color: DesignTokens.border),
          ),
          color: DesignTokens.surface,
          child: Column(
            children: [
              for (var i = 0; i < porMetodo.length; i++) ...[
                if (i > 0) const Divider(height: 1),
                Padding(
                  padding: DesignTokens.paddingAll('sm'),
                  child: Row(
                    children: [
                      Expanded(child: Text(_metodoTexto(porMetodo.keys.elementAt(i)), style: DesignTokens.style('bodyMedium'))),
                      Text('Bs ${_fmt.format(porMetodo.values.elementAt(i))}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  // -------------------------------------------------------------- Productos
  Widget _buildProductos() {
    // Agrupar unidades vendidas y total por producto.
    final mapa = <String, Map<String, dynamic>>{};
    for (final v in _ventas) {
      for (final item in v.productos) {
        final clave = item.codigo.isNotEmpty ? item.codigo : item.nombre;
        final previo = mapa[clave];
        if (previo == null) {
          mapa[clave] = {
            'nombre': item.nombre.isNotEmpty ? item.nombre : item.codigo,
            'cantidad': item.cantidad,
            'usd': item.cantidad * item.precioUsd,
          };
        } else {
          previo['cantidad'] = previo['cantidad'] + item.cantidad;
          previo['usd'] = previo['usd'] + item.cantidad * item.precioUsd;
        }
      }
    }
    if (mapa.isEmpty) {
      return const EmptyState(
        icon: Icons.inventory_2_outlined,
        title: 'Sin productos vendidos',
        message: 'No hay ventas en el periodo seleccionado',
      );
    }

    final filas = mapa.values.toList()
      ..sort((a, b) => (b['cantidad'] as double).compareTo(a['cantidad'] as double));
    final tasa = widget.state.exchangeRate;

    return ListView.builder(
      padding: DesignTokens.paddingAll('md'),
      itemCount: filas.length,
      itemBuilder: (ctx, i) {
        final f = filas[i];
        final usd = f['usd'] as double;
        return Card(
          elevation: 0,
          margin: DesignTokens.paddingOnly(bottom: 'sm'),
          shape: RoundedRectangleBorder(
            borderRadius: DesignTokens.borderRadius('md'),
            side: BorderSide(color: DesignTokens.border),
          ),
          color: DesignTokens.surface,
          child: ListTile(
            title: Text('${f['nombre']}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis),
            subtitle: Text('${_cantidad(f['cantidad'] as double)} vendidas', style: DesignTokens.style('bodySmall')),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(tasa > 0 ? 'Bs ${_fmt.format(usd * tasa)}' : 'Bs ${_fmt.format(usd)}', style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
                Text('\$${_fmt.format(usd)}', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
              ],
            ),
          ),
        );
      },
    );
  }

  // ------------------------------------------------------------------ Stock
  Widget _buildStock() {
    // products es un Map<codigo, Product>; .values para poder filtrar la lista.
    final criticos = widget.state.products.values.where((p) {
      final stock = widget.state.calculateStock(p.codigo);
      return stock <= p.stockMinimo;
    }).toList()
      ..sort((a, b) => widget.state.calculateStock(a.codigo).compareTo(widget.state.calculateStock(b.codigo)));

    if (criticos.isEmpty) {
      return const EmptyState(
        icon: Icons.check_circle_outline,
        title: 'Stock bajo control',
        message: 'Ningún producto está en su stock mínimo',
      );
    }

    return ListView.builder(
      padding: DesignTokens.paddingAll('md'),
      itemCount: criticos.length,
      itemBuilder: (ctx, i) {
        final p = criticos[i];
        final stock = widget.state.calculateStock(p.codigo);
        return Card(
          elevation: 0,
          margin: DesignTokens.paddingOnly(bottom: 'sm'),
          shape: RoundedRectangleBorder(
            borderRadius: DesignTokens.borderRadius('md'),
            side: BorderSide(color: DesignTokens.warningLight, width: 1.5),
          ),
          color: DesignTokens.surface,
          child: ListTile(
            title: Text(p.nombre, style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold), overflow: TextOverflow.ellipsis),
            subtitle: Text('${p.codigo} · Mínimo: ${_cantidad(p.stockMinimo)}', style: DesignTokens.style('bodySmall')),
            trailing: Text(
              _cantidad(stock),
              style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.warning),
            ),
          ),
        );
      },
    );
  }

  // ---------------------------------------------------------------- Helpers
  double _saldoUsd(Sale s) {
    if (s.saldoPendienteUsd > 0) return s.saldoPendienteUsd;
    if (widget.state.exchangeRate > 0) return s.saldoPendiente / widget.state.exchangeRate;
    return 0;
  }

  String _cantidad(double v) {
    return v.truncateToDouble() == v ? v.toStringAsFixed(0) : v.toStringAsFixed(2);
  }

  String _metodoTexto(String metodo) {
    switch (metodo) {
      case 'efectivo':
        return 'Efectivo';
      case 'divisas':
        return 'Divisas';
      case 'tarjeta':
        return 'Tarjeta';
      case 'pago_movil':
      case 'pago movil':
        return 'Pago Móvil';
      case 'mixto':
        return 'Pago Mixto';
      case 'credito':
      case 'fiado':
        return 'Fiados / Créditos';
      default:
        return metodo;
    }
  }

  Widget _kpi(String titulo, String valor, String detalle, {Color? color}) {
    return Container(
      padding: DesignTokens.paddingAll('sm'),
      decoration: BoxDecoration(
        color: DesignTokens.surface,
        borderRadius: DesignTokens.borderRadius('md'),
        border: Border.all(color: DesignTokens.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(titulo, style: DesignTokens.style('labelSmall').copyWith(color: DesignTokens.textMuted, fontWeight: FontWeight.bold)),
          Text(valor, style: DesignTokens.style('titleSmall').copyWith(fontWeight: FontWeight.bold, color: color ?? DesignTokens.text), overflow: TextOverflow.ellipsis),
          Text(detalle, style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted), overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }
}