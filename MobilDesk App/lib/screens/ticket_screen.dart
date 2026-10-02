import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/design_tokens.dart';

/// Ticket de venta de la App.
///
/// Replica el ticket que imprime la PC: datos del negocio, detalle de
/// productos, totales, forma de pago y el saldo pendiente del fiado.
///
/// El ticket se genera en texto con el formato de 80mm de una impresora térmica
/// y se puede copiar o enviar por WhatsApp/correo. No se genera PDF porque
/// exigiria una dependencia nativa nueva (`printing`), que no se quiere
/// introducir en una version ya publicada.
class TicketScreen extends StatelessWidget {
  final AppState state;
  final Sale sale;
  final String? nombreNegocio;
  final String? mensajeTicket;

  const TicketScreen({
    super.key,
    required this.state,
    required this.sale,
    this.nombreNegocio,
    this.mensajeTicket,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DesignTokens.background,
      appBar: AppBar(
        backgroundColor: DesignTokens.secondary,
        foregroundColor: DesignTokens.textOnPrimary,
        title: Text('Ticket de Venta', style: DesignTokens.style('titleLarge').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textOnPrimary)),
        actions: [
          IconButton(
            tooltip: 'Copiar',
            icon: const Icon(Icons.copy_rounded),
            onPressed: () => _copiar(context),
          ),
          IconButton(
            tooltip: 'Enviar',
            icon: const Icon(Icons.share_rounded),
            onPressed: () => _compartir(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: DesignTokens.paddingAll('md'),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: DesignTokens.borderRadius('lg'),
                side: BorderSide(color: DesignTokens.border),
              ),
              color: DesignTokens.surface,
              child: Padding(
                padding: DesignTokens.paddingAll('md'),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _encabezado(),
                    Divider(height: DesignTokens.spaceLg),
                    _lineaFactura(),
                    Divider(height: DesignTokens.spaceMd),
                    _detalleProductos(),
                    Divider(height: DesignTokens.spaceMd),
                    _totales(),
                    if (sale.esFiada) ...[
                      Divider(height: DesignTokens.spaceMd),
                      _bloqueFiado(),
                    ],
                    if (mensajeTicket != null && mensajeTicket!.trim().isNotEmpty) ...[
                      Divider(height: DesignTokens.spaceMd),
                      Text(
                        mensajeTicket!.trim(),
                        textAlign: TextAlign.center,
                        style: DesignTokens.style('bodySmall').copyWith(
                          color: DesignTokens.textMuted,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------- Partes
  Widget _encabezado() {
    return Column(
      children: [
        Text(
          _nombre,
          textAlign: TextAlign.center,
          style: DesignTokens.style('titleMedium').copyWith(fontWeight: FontWeight.bold),
        ),
        Text(
          'N° ${sale.numeroFactura}',
          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
        ),
        Text(
          DateFormat('dd/MM/yyyy  hh:mm a', 'es_VE').format(DateTime.tryParse(sale.fecha) ?? DateTime.now()),
          style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
        ),
      ],
    );
  }

  Widget _lineaFactura() {
    return Column(
      children: [
        _fila('Factura', sale.numeroFactura, negrita: true),
        _fila('Tasa', 'Bs ${_fmt.format(sale.tasa)} / USD'),
      ],
    );
  }

  Widget _detalleProductos() {
    if (sale.productos.isEmpty) {
      return Text(
        'Sin detalle de productos.',
        style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('PRODUCTOS', style: DesignTokens.style('labelSmall').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.textMuted)),
        SizedBox(height: DesignTokens.spaceSm),
        for (final p in sale.productos)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${_cantidad(p.cantidad)} x ${p.nombre.isNotEmpty ? p.nombre : p.codigo}',
                  style: DesignTokens.style('bodySmall'),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '  Bs ${_fmt.format(p.precioUsd)} c/u',
                      style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
                    ),
                    Text(
                      'Bs ${_fmt.format(p.cantidad * p.precioUsd * sale.tasa)}',
                      style: DesignTokens.style('bodySmall').copyWith(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _totales() {
    return Column(
      children: [
        _fila('Subtotal Bs', _fmt.format(sale.totalBs)),
        _fila('Subtotal USD', '\$${_fmt.format(sale.totalUsd)}'),
        Divider(height: DesignTokens.spaceSm),
        _fila('TOTAL Bs', _fmt.format(sale.totalBs), negrita: true, grande: true),
        _fila('TOTAL USD', '\$${_fmt.format(sale.totalUsd)}', negrita: true),
        SizedBox(height: DesignTokens.spaceSm),
        _fila('Método de pago', _metodoTexto(sale.metodoPago), negrita: true),
      ],
    );
  }

  Widget _bloqueFiado() {
    final saldoBs = sale.saldoPendiente;
    final saldoUsd = sale.saldoPendienteUsd > 0
        ? sale.saldoPendienteUsd
        : (state.exchangeRate > 0 ? saldoBs / state.exchangeRate : 0.0);
    return Container(
      padding: DesignTokens.paddingAll('sm'),
      decoration: BoxDecoration(
        color: DesignTokens.surfaceVariant,
        borderRadius: DesignTokens.borderRadius('md'),
        border: Border.all(color: DesignTokens.warning),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'SALDO PENDIENTE (FIADO)',
            style: DesignTokens.style('labelSmall').copyWith(fontWeight: FontWeight.bold, color: DesignTokens.warning),
          ),
          SizedBox(height: 2),
          _fila('Cliente', (sale.clienteNombre ?? '').isEmpty ? 'Sin nombre' : sale.clienteNombre!, negrita: true),
          _fila('Saldo Bs', _fmt.format(saldoBs), negrita: true),
          _fila('Saldo USD', '\$${_fmt.format(saldoUsd)}'),
          Text(
            'Valorizado a la tasa vigente: Bs ${_fmt.format(state.exchangeRate)}',
            style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted),
          ),
        ],
      ),
    );
  }

  Widget _fila(String etiqueta, String valor, {bool negrita = false, bool grande = false}) {
    final estilo = (grande ? DesignTokens.style('titleMedium') : DesignTokens.style('bodyMedium'))
        .copyWith(fontWeight: negrita ? FontWeight.bold : FontWeight.normal);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(etiqueta, style: estilo.copyWith(color: DesignTokens.textSecondary)),
          Text(valor, style: estilo),
        ],
      ),
    );
  }

  // ------------------------------------------------------------- Acciones
  String get _nombre {
    if (nombreNegocio != null && nombreNegocio!.trim().isNotEmpty) return nombreNegocio!;
    return state.businessName.isNotEmpty ? state.businessName : 'Mi Negocio';
  }

  Future<void> _copiar(BuildContext context) async {
    await Clipboard.setData(ClipboardData(text: _textoTicket()));
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ticket copiado al portapapeles')),
      );
    }
  }

  /// Abre el menú de compartir del sistema con el ticket en texto.
  Future<void> _compartir(BuildContext context) async {
    // Se comprueba 'mounted' tras cada await para no usar un context invalido.
    final navigator = Navigator.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final texto = _textoTicket();
    // wa.me permite abrir WhatsApp con el mensaje ya escrito, que es el uso
    // más común en un negocio. Si no está, se recurre al menú del sistema.
    final uri = Uri.parse('https://wa.me/?text=${Uri.encodeComponent(texto)}');
    try {
      final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (ok) return;
    } catch (_) {
      // Continuar al portapapeles.
    }
    // Copiar en vez de navegar: el context pudo quedar obsoleto tras el await.
    await Clipboard.setData(ClipboardData(text: texto));
    messenger.showSnackBar(
      const SnackBar(content: Text('Ticket copiado al portapapeles')),
    );
    if (navigator.mounted) navigator.pop();
  }

  /// Ticket en texto plano, con el ancho de una impresora térmica de 80mm.
  String _textoTicket() {
    final l = <String>[];
    l.add(_nombre);
    l.add('N° ${sale.numeroFactura}');
    l.add(DateFormat('dd/MM/yyyy hh:mm a', 'es_VE').format(DateTime.tryParse(sale.fecha) ?? DateTime.now()));
    l.add('-' * 32);
    for (final p in sale.productos) {
      l.add('${_cantidad(p.cantidad)} x ${p.nombre.isNotEmpty ? p.nombre : p.codigo}');
      l.add('    Bs ${_fmt.format(p.cantidad * p.precioUsd * sale.tasa)}');
    }
    l.add('-' * 32);
    l.add('TOTAL      Bs ${_fmt.format(sale.totalBs)}');
    l.add('TOTAL     USD \$${_fmt.format(sale.totalUsd)}');
    l.add('PAGO: ${_metodoTexto(sale.metodoPago)}');
    if (sale.esFiada) {
      l.add('-' * 32);
      l.add('FIADO CLIENTE: ${(sale.clienteNombre ?? '').isEmpty ? 'Sin nombre' : sale.clienteNombre}');
      l.add('SALDO Bs ${_fmt.format(sale.saldoPendiente)}');
    }
    if (mensajeTicket != null && mensajeTicket!.trim().isNotEmpty) {
      l.add('');
      l.add(mensajeTicket!.trim());
    }
    return l.join('\n');
  }

  // --------------------------------------------------------------- Helpers
  /// NumberFormat no puede ser un campo final en una clase con constructor
  /// const, asi que se crea bajo demanda.
  NumberFormat get _fmt => NumberFormat('#,##0.00', 'es_VE');

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
}