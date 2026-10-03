/// Extension para usar double como SizedBox.
import 'package:flutter/material.dart';

/// Extension para usar double como SizedBox
extension SizedBoxExtension on double {
  SizedBox get width => SizedBox(width: this);
  SizedBox get height => SizedBox(height: this);
}
