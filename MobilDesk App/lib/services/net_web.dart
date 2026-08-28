import 'package:http/http.dart' as http;

/// Cliente HTTP para web (navegador), compatible con CORS de Supabase.
Future<String> fetchRaw(String url,
    {String method = 'GET',
    Map<String, String> headers = const {},
    String? body,
    Duration timeout = const Duration(seconds: 15)}) async {
  final uri = Uri.parse(url);
  final request = http.Request(method, uri);
  headers.forEach((k, v) => request.headers[k] = v);
  if (body != null) {
    request.headers['Content-Type'] = 'application/json';
    request.body = body;
  }
  final response =
      await http.Response.fromStream(await request.send().timeout(timeout));
  final text = response.body;
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw 'HTTP ${response.statusCode}: $text';
  }
  return text;
}
