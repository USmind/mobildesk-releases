import 'dart:io';
import 'dart:convert';

/// Cliente HTTP para plataformas nativas (Android/Windows/iOS).
Future<String> fetchRaw(String url,
    {String method = 'GET',
    Map<String, String> headers = const {},
    String? body,
    Duration timeout = const Duration(seconds: 15)}) async {
  final client = HttpClient()
    ..badCertificateCallback = (cert, host, port) => true;
  try {
    final request = await client.openUrl(method, Uri.parse(url)).timeout(timeout);
    headers.forEach(request.headers.set);
    if (body != null) {
      final bytes = utf8.encode(body);
      request.contentLength = bytes.length;
      request.add(bytes);
    }
    final response = await request.close().timeout(timeout);
    final text = await response.transform(utf8.decoder).join();
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw 'HTTP ${response.statusCode}: $text';
    }
    return text;
  } finally {
    client.close();
  }
}
