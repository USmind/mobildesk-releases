import 'package:flutter/material.dart';
import '../services/app_state.dart';
import 'dashboard_screen.dart';
import 'pos_screen.dart';
import 'products_screen.dart';
import 'sales_history_screen.dart';
import 'settings_screen.dart';
import 'license_blocked_screen.dart';
import '../theme/design_tokens.dart';

class MainNavigationScreen extends StatefulWidget {
  final AppState state;
  const MainNavigationScreen({super.key, required this.state});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  void _onNavigateTab(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  Widget _buildScreen() {
    if (widget.state.licenciaBloqueada) {
      return LicenseBlockedScreen(state: widget.state);
    }
    switch (_currentIndex) {
      case 0:
        return DashboardScreen(state: widget.state, onNavigateTab: _onNavigateTab);
      case 1:
        return PosScreen(state: widget.state);
      case 2:
        return ProductsScreen(state: widget.state);
      case 3:
        return SalesHistoryScreen(
          state: widget.state,
          onFiarMas: (clientName) {
            widget.state.clienteParaFiar = clientName;
            _onNavigateTab(1);
          },
        );
      case 4:
        return SettingsScreen(state: widget.state);
      default:
        return DashboardScreen(state: widget.state, onNavigateTab: _onNavigateTab);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListenableBuilder(
        listenable: widget.state,
        builder: (context, _) => _buildScreen(),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        backgroundColor: DesignTokens.surface,
        elevation: 0,
        indicatorColor: DesignTokens.primaryContainer,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded, color: DesignTokens.primaryDark),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.point_of_sale_outlined),
            selectedIcon: Icon(Icons.point_of_sale_rounded, color: DesignTokens.primaryDark),
            label: 'Vender',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2_rounded, color: DesignTokens.primaryDark),
            label: 'Inventario',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long_rounded, color: DesignTokens.primaryDark),
            label: 'Ventas',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings_rounded, color: DesignTokens.primaryDark),
            label: 'Ajustes',
          ),
        ],
      ),
    );
  }
}
