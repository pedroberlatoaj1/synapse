const double easeFactorMin = 1.30;
const int intervalMaxDays = 36500;
const int intervalMinAfterSuccess = 1;

const Set<String> validStates = {'new', 'learning', 'review', 'lapsed'};
const Set<String> validRatings = {'again', 'hard', 'good', 'easy'};

const Map<String, String> _successTransitions = {
  'new': 'learning',
  'learning': 'review',
  'review': 'review',
  'lapsed': 'review',
};

Map<String, Object> calculateNextState({
  required String state,
  required double easeFactor,
  required int intervalDays,
  required int repetitions,
  required String rating,
}) {
  if (!validStates.contains(state)) {
    throw ArgumentError.value(state, 'state', 'Invalid state');
  }
  if (!validRatings.contains(rating)) {
    throw ArgumentError.value(rating, 'rating', 'Invalid rating');
  }

  if (rating == 'again') {
    final newEase = _maxDouble(easeFactorMin, easeFactor * 0.85);
    return {
      'state': state == 'review' ? 'lapsed' : 'learning',
      'ease_factor': newEase,
      'interval_days': 0,
      'repetitions': 0,
    };
  }

  final int newInterval;
  final double newEase;

  if (rating == 'hard') {
    newInterval = _successInterval(intervalDays * 1.2);
    newEase = _maxDouble(easeFactorMin, easeFactor - 0.15);
  } else if (rating == 'good') {
    newInterval = _successInterval(intervalDays * easeFactor);
    newEase = easeFactor;
  } else {
    newInterval = _successInterval(intervalDays * easeFactor * 1.3);
    newEase = easeFactor + 0.15;
  }

  return {
    'state': _successTransitions[state]!,
    'ease_factor': newEase,
    'interval_days': newInterval,
    'repetitions': repetitions + 1,
  };
}

int _successInterval(double value) {
  final rounded = _roundHalfToEven(value);
  final floored = rounded < intervalMinAfterSuccess
      ? intervalMinAfterSuccess
      : rounded;
  return floored > intervalMaxDays ? intervalMaxDays : floored;
}

int _roundHalfToEven(double value) {
  if (!value.isFinite) {
    throw ArgumentError.value(value, 'value', 'Cannot round non-finite value');
  }

  final truncated = value.truncate();
  final fraction = value - truncated;
  if (fraction.abs() == 0.5) {
    if (truncated.isEven) {
      return truncated;
    }
    return value.isNegative ? truncated - 1 : truncated + 1;
  }

  return value.round();
}

double _maxDouble(double a, double b) => a > b ? a : b;
