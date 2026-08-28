export 'net_io.dart'
    if (dart.library.js) 'net_web.dart'
    if (dart.library.html) 'net_web.dart';
