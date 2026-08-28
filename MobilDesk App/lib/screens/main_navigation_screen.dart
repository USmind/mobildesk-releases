import 'package:flutter/material.dart';
import '../services/app_state.dart';
import 'dashboard_screen.dart';
import 'pos_screen.dart';
import 'products_screen.dart';
import 'sales_history_screen.dart';
import 'settings_screen.dart';
import 'license_blocked_screen.dart';

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

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.state,
      builder: (context, _) {
        // Bloqueo de licencia: identico al programa de PC.
        if (widget.state.licenciaBloqueada) {
          return LicenseBlockedScreen(state: widget.state);
        }
        return _buildMainScaffold();
      },
    );
  }

  Widget _buildMainScaffold() {
    final screens = [
      DashboardScreen(state: widget.state, onNavigateTab: _onNavigateTab),
      PosScreen(state: widget.state),
      ProductsScreen(state: widget.state),
      SalesHistoryScreen(state: widget.state),
      SettingsScreen(state: widget.state),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        backgroundColor: Colors.white,
        elevation: 4,
        indicatorColor: const Color(0xFFDBEAFE),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded, color: Color(0xFF1D4ED8)),
            label: 'Inicio',
          ),
          NavigationDestination(
            icon: Icon(Icons.point_of_sale_outlined),
            selectedIcon: Icon(Icons.point_of_sale_rounded, color: Color(0xFF1D4ED8)),
            label: 'Vender',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2_rounded, color: Color(0xFF1D4ED8)),
            label: 'Inventario',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long_rounded, color: Color(0xFF1D4ED8)),
            label: 'Ventas',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings_rounded, color: Color(0xFF1D4ED8)),
            label: 'Ajustes',
          ),
        ],
      ),
    );
  }
}
