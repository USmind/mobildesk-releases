/// Configuración centralizada para MobilDesk App (Flutter).
/// Los valores se inyectan en tiempo de compilación con --dart-define
/// o se leen de variables de entorno en desarrollo.

const String kSupabaseUrl = String.fromEnvironment(
  'SUPABASE_URL',
  defaultValue: 'https://atxeuhqhariymdqsbmpd.supabase.co',
);

const String kSupabaseKey = String.fromEnvironment(
  'SUPABASE_KEY',
  defaultValue: 'sb_publishable_6a_o_Jv_XhqZE9TP7mO2EA_gOeak-mL',
);

const String kVersionJsonUrl = String.fromEnvironment(
  'VERSION_JSON_URL',
  defaultValue: 'https://raw.githubusercontent.com/USmind/mobildesk-releases/main/version.json',
);

/// Verifica si estamos en modo debug (para certificados auto-firmados)
bool get isDebugMode {
  bool debug = false;
  assert(debug = true);
  return debug;
}