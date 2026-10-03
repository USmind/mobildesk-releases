import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../theme/design_tokens.dart';
import '../utils.dart';
import '../screens/ticket_screen.dart';

/// Muestra el detalle de una venta en un dialogo.
///
/// Es la misma ventana que se abre al tocar una factura, tanto desde la
/// pestana Ventas como desde la lista de ventas recientes del inicio.
/// Antes solo existia dentro de la pantalla de historial, asi que tocar una
/// factura en el inicio no hacia nada.
Future<void> showSaleDetailDialog(BuildContext context, AppState state, Sale sale) {
  final fmt = NumberFormat('#,##0.00', 'es_VE');
  final pd = sale.pagosDetalle;
  return showDialog(
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
                          'Bs ${fmt.format(p.cantidad * p.precioUsd * sale.tasa)}',
                          style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  )),
            const Divider(height: 12),
            Text('Total: Bs ${fmt.format(sale.totalBs)} (\$${fmt.format(sale.totalUsd)})',
                style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold)),
            Text('Tasa: Bs ${fmt.format(sale.tasa)}',
                style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
            if (pd != null && sale.metodoPago == 'mixto') ...[
              DesignTokens.spaceXs.height,
              if (pd.divisasUsd > 0)
                Text('  • Divisas: \$${fmt.format(pd.divisasUsd)}', style: DesignTokens.style('bodySmall')),
              if (pd.efectivoBs > 0)
                Text('  • Efectivo: Bs ${fmt.format(pd.efectivoBs)}', style: DesignTokens.style('bodySmall')),
              if (pd.pagoMovilBs > 0)
                Text('  • Pago Móvil: Bs ${fmt.format(pd.pagoMovilBs)}', style: DesignTokens.style('bodySmall')),
              if (pd.tarjetaBs > 0)
                Text('  • Tarjeta: Bs ${fmt.format(pd.tarjetaBs)}', style: DesignTokens.style('bodySmall')),
              if (pd.fiadoBs > 0)
                Text('  • Fiado: Bs ${fmt.format(pd.fiadoBs)}', style: DesignTokens.style('bodySmall')),
            ],
            if (sale.esFiada) ...[
              DesignTokens.spaceXs.height,
              Text('Saldo pendiente: Bs ${fmt.format(sale.saldoPendiente)}',
                  style: DesignTokens.style('bodyMedium').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.warning)),
            ],
            if (sale.vueltoBs > 0)
              Text('Vuelto: Bs ${fmt.format(sale.vueltoBs)}',
                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.success)),
            if (sale.vueltoUsd > 0)
              Text('Vuelto: \$${fmt.format(sale.vueltoUsd)}',
                  style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.success)),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.pop(ctx);
            Navigator.push(
              ctx,
              MaterialPageRoute(
                builder: (_) => TicketScreen(state: state, sale: sale),
              ),
            );
          },
          child: Text('Ver Ticket', style: DesignTokens.style('labelLarge')),
        ),
        FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cerrar')),
      ],
    ),
  );
}