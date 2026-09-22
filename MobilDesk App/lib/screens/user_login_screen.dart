import 'package:flutter/material.dart';
import '../theme/design_tokens.dart';
import '../services/app_state.dart';

class UserLoginScreen extends StatefulWidget {
  final AppState state;
  const UserLoginScreen({super.key, required this.state});

  @override
  State<UserLoginScreen> createState() => _UserLoginScreenState();
}

class _UserLoginScreenState extends State<UserLoginScreen> {
  String? _selectedUser;
  final _passCtrl = TextEditingController();
  bool _keep = true;
  bool _loading = false;
  bool _obscure = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => widget.state.fetchAppUsers());
  }

  @override
  void dispose() {
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_selectedUser == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Elige un usuario.')));
      return;
    }
    if (_passCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Escribe la contraseña.')));
      return;
    }
    setState(() => _loading = true);
    final ok = await widget.state.loginAppUser(_selectedUser!, _passCtrl.text, keepLogged: _keep);
    if (!mounted) return;
    setState(() => _loading = false);
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Contraseña incorrecta.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DesignTokens.background,
      body: Center(
        child: SingleChildScrollView(
          padding: DesignTokens.paddingSymmetric(h: 'xl', v: '2xl'),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(Icons.lock_rounded, size: 56, color: DesignTokens.primary),
                const SizedBox(height: 12),
                Text('Iniciar Sesión', textAlign: TextAlign.center, style: DesignTokens.style('headlineMedium').copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text('Elige tu usuario y escribe tu contraseña (igual que en la PC). Sesión independiente por dispositivo.', textAlign: TextAlign.center, style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted)),
                const SizedBox(height: 24),
                Card(
                  elevation: 0,
                  color: DesignTokens.surface,
                  shape: RoundedRectangleBorder(borderRadius: DesignTokens.borderRadius('xl'), side: BorderSide(color: DesignTokens.border)),
                  child: Padding(
                    padding: DesignTokens.paddingAll('xl'),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AnimatedBuilder(
                          animation: widget.state,
                          builder: (_, __) {
                            final users = widget.state.appUsers;
                            if (users.isEmpty) {
                              return Text('Cargando usuarios...', style: DesignTokens.style('bodySmall').copyWith(color: DesignTokens.textMuted));
                            }
                            return DropdownButtonFormField<String>(
                              value: _selectedUser,
                              hint: const Text('Elige usuario'),
                              items: users.map<DropdownMenuItem<String>>((u) {
                                final username = (u['username'] ?? '').toString();
                                final nombre = (u['nombre'] ?? username).toString();
                                final role = (u['role'] ?? '').toString();
                                return DropdownMenuItem(value: username, child: Text('$nombre ($username) — $role'));
                              }).toList(),
                              onChanged: (v) => setState(() => _selectedUser = v),
                              decoration: InputDecoration(labelText: 'Usuario', prefixIcon: Icon(Icons.person_rounded, color: DesignTokens.primary)),
                            );
                          },
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _passCtrl,
                          obscureText: _obscure,
                          decoration: InputDecoration(
                            labelText: 'Contraseña',
                            prefixIcon: Icon(Icons.key_rounded, color: DesignTokens.primary),
                            suffixIcon: IconButton(icon: Icon(_obscure ? Icons.visibility_off_rounded : Icons.visibility_rounded), onPressed: () => setState(() => _obscure = !_obscure)),
                          ),
                          onSubmitted: (_) => _login(),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Checkbox(value: _keep, onChanged: (v) => setState(() => _keep = v ?? true), activeColor: DesignTokens.primary),
                            Expanded(child: Text('Mantener sesión iniciada en este dispositivo', style: DesignTokens.style('bodySmall'))),
                          ],
                        ),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: _loading ? null : _login,
                          style: FilledButton.styleFrom(backgroundColor: DesignTokens.primary, padding: const EdgeInsets.symmetric(vertical: 16)),
                          child: _loading ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white)) : const Text('Ingresar', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
