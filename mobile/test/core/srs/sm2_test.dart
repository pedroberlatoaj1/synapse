import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:synapse_mobile/core/srs/sm2.dart';

void main() {
  test('matches backend SM-2 fixtures', () {
    final fixturesFile = _fixtureFile();
    final fixtures =
        jsonDecode(fixturesFile.readAsStringSync()) as Map<String, Object?>;
    final cases = fixtures['cases']! as List<Object?>;

    for (final fixtureCase in cases) {
      final data = fixtureCase! as Map<String, Object?>;
      final input = data['input']! as Map<String, Object?>;
      final expected = data['expected']! as Map<String, Object?>;

      final actual = calculateNextState(
        state: input['state']! as String,
        easeFactor: (input['ease_factor']! as num).toDouble(),
        intervalDays: input['interval_days']! as int,
        repetitions: input['repetitions']! as int,
        rating: input['rating']! as String,
      );

      expect(
        actual,
        equals(expected),
        reason: 'Fixture ${data['name']} must match backend Python output.',
      );
    }
  });
}

File _fixtureFile() {
  final mobileRelative = File('docs/sm2_fixtures.json');
  if (mobileRelative.existsSync()) {
    return mobileRelative;
  }

  return File('mobile/docs/sm2_fixtures.json');
}
