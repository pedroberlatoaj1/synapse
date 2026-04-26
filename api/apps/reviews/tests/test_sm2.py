"""Unit tests for the pure SM-2 engine.

NO Django, NO ORM, NO @pytest.mark.django_db — these tests run entirely
in memory and finish in sub-millisecond range. The whole point of
isolating sm2.py from infrastructure is that the algorithm's invariants
can be exercised exhaustively (boundary chains, all rating x state
combinations) without paying database setup cost.

If you find yourself reaching for a Django fixture in this file,
something has leaked from the API layer into the engine — fix that
instead of weakening this isolation.
"""
from __future__ import annotations

import pytest

from apps.reviews.sm2 import (
    EASE_FACTOR_MIN,
    INTERVAL_MAX_DAYS,
    calculate_next_state,
)

# --- 1) Input validation ---------------------------------------------------


def test_invalid_state_raises_valueerror():
    with pytest.raises(ValueError, match="Invalid state"):
        calculate_next_state("bogus", 2.5, 10, 3, "good")


def test_invalid_rating_raises_valueerror():
    with pytest.raises(ValueError, match="Invalid rating"):
        calculate_next_state("review", 2.5, 10, 3, "perfect")


# --- 2) Output shape -------------------------------------------------------


def test_return_dict_has_exact_keys():
    result = calculate_next_state("review", 2.5, 10, 3, "good")
    assert set(result.keys()) == {"state", "ease_factor", "interval_days", "repetitions"}


# --- 3) "again" branch -----------------------------------------------------


def test_again_from_review_transitions_to_lapsed():
    result = calculate_next_state("review", 2.5, 10, 3, "again")
    assert result["state"] == "lapsed"


def test_again_from_learning_stays_in_learning():
    result = calculate_next_state("learning", 2.5, 1, 1, "again")
    assert result["state"] == "learning"


def test_again_from_new_goes_to_learning():
    result = calculate_next_state("new", 2.5, 0, 0, "again")
    assert result["state"] == "learning"


def test_again_from_lapsed_goes_to_learning():
    # Per spec: state is "lapsed" only when previous was "review";
    # everything else (including a re-lapse) routes to "learning".
    result = calculate_next_state("lapsed", 2.0, 0, 0, "again")
    assert result["state"] == "learning"


def test_again_resets_interval_and_repetitions():
    result = calculate_next_state("review", 2.5, 30, 7, "again")
    assert result["interval_days"] == 0
    assert result["repetitions"] == 0


def test_again_multiplies_ease_factor_by_zero_eighty_five():
    result = calculate_next_state("review", 2.0, 10, 3, "again")
    assert result["ease_factor"] == pytest.approx(2.0 * 0.85)


# --- 4) ease_factor floor (the most important boundary) -------------------


def test_ease_factor_never_drops_below_floor_after_many_consecutive_agains():
    # Mathematically 2.5 * 0.85^N converges to 0; the engine must clamp.
    # 100 iterations is overkill — convergence to the floor happens around
    # iteration 5 — but the chain proves the floor is sticky, not just
    # applied once.
    ef = 2.5
    for _ in range(100):
        result = calculate_next_state("review", ef, 10, 5, "again")
        ef = result["ease_factor"]
        assert ef >= EASE_FACTOR_MIN
    assert ef == pytest.approx(EASE_FACTOR_MIN)


def test_ease_factor_at_floor_stays_at_floor_on_again():
    result = calculate_next_state("review", EASE_FACTOR_MIN, 10, 3, "again")
    assert result["ease_factor"] == pytest.approx(EASE_FACTOR_MIN)


def test_hard_clamps_ease_factor_at_floor():
    # 1.40 - 0.15 = 1.25, must clamp UP to 1.30.
    result = calculate_next_state("review", 1.40, 10, 3, "hard")
    assert result["ease_factor"] == pytest.approx(EASE_FACTOR_MIN)


def test_hard_at_floor_stays_at_floor():
    result = calculate_next_state("review", EASE_FACTOR_MIN, 10, 3, "hard")
    assert result["ease_factor"] == pytest.approx(EASE_FACTOR_MIN)


def test_hard_alternated_with_again_never_breaks_floor():
    # Adversarial sequence: 50 alternations of hard/again starting at
    # the floor. Both paths apply ease-reducing math; the floor must
    # hold across the whole chain.
    ef = EASE_FACTOR_MIN
    ratings = ["hard", "again"] * 50
    for r in ratings:
        result = calculate_next_state("review", ef, 10, 3, r)
        ef = result["ease_factor"]
        assert ef >= EASE_FACTOR_MIN


# --- 5) "hard" branch ------------------------------------------------------


def test_hard_multiplies_interval_by_one_point_two_and_rounds():
    # 10 * 1.2 = 12.0
    result = calculate_next_state("review", 2.5, 10, 3, "hard")
    assert result["interval_days"] == 12


def test_hard_on_zero_interval_floors_at_one_day():
    # round(0 * 1.2) = 0 — without the floor a fresh card rated 'hard'
    # would re-appear immediately.
    result = calculate_next_state("learning", 2.5, 0, 0, "hard")
    assert result["interval_days"] == 1


def test_hard_subtracts_zero_point_fifteen_from_ease_when_above_floor():
    result = calculate_next_state("review", 2.5, 10, 3, "hard")
    assert result["ease_factor"] == pytest.approx(2.35)


def test_hard_increments_repetitions():
    result = calculate_next_state("review", 2.5, 10, 3, "hard")
    assert result["repetitions"] == 4


# --- 6) "good" branch ------------------------------------------------------


def test_good_multiplies_interval_by_ease_and_rounds():
    # 4 * 2.5 = 10.0 — picked to avoid banker's-rounding half-ties.
    result = calculate_next_state("review", 2.5, 4, 2, "good")
    assert result["interval_days"] == 10


def test_good_on_zero_interval_floors_at_one_day():
    # New card's first 'good' rating produces interval=1, not 0.
    result = calculate_next_state("new", 2.5, 0, 0, "good")
    assert result["interval_days"] == 1


def test_good_leaves_ease_factor_unchanged():
    result = calculate_next_state("review", 2.5, 4, 2, "good")
    assert result["ease_factor"] == pytest.approx(2.5)


def test_good_increments_repetitions():
    result = calculate_next_state("review", 2.5, 4, 2, "good")
    assert result["repetitions"] == 3


# --- 7) "easy" branch ------------------------------------------------------


def test_easy_multiplies_interval_by_ease_times_one_point_three():
    # 10 * 2.6 * 1.3 = 33.8 -> round = 34. Clean half-tie-free choice.
    result = calculate_next_state("review", 2.6, 10, 3, "easy")
    assert result["interval_days"] == 34


def test_easy_adds_zero_point_fifteen_to_ease():
    result = calculate_next_state("review", 2.5, 10, 3, "easy")
    assert result["ease_factor"] == pytest.approx(2.65)


def test_easy_on_zero_interval_floors_at_one_day():
    result = calculate_next_state("new", 2.5, 0, 0, "easy")
    assert result["interval_days"] == 1


def test_easy_increments_repetitions():
    result = calculate_next_state("review", 2.5, 10, 3, "easy")
    assert result["repetitions"] == 4


# --- 8) Successful-rating state transitions -------------------------------


@pytest.mark.parametrize("rating", ["hard", "good", "easy"])
def test_new_on_success_transitions_to_learning(rating):
    result = calculate_next_state("new", 2.5, 0, 0, rating)
    assert result["state"] == "learning"


@pytest.mark.parametrize("rating", ["hard", "good", "easy"])
def test_learning_on_success_transitions_to_review(rating):
    result = calculate_next_state("learning", 2.5, 1, 1, rating)
    assert result["state"] == "review"


@pytest.mark.parametrize("rating", ["hard", "good", "easy"])
def test_review_on_success_stays_review(rating):
    result = calculate_next_state("review", 2.5, 10, 3, rating)
    assert result["state"] == "review"


@pytest.mark.parametrize("rating", ["hard", "good", "easy"])
def test_lapsed_on_success_transitions_to_review(rating):
    result = calculate_next_state("lapsed", 2.0, 1, 0, rating)
    assert result["state"] == "review"


# --- 9) Interval ceiling --------------------------------------------------


def test_interval_clamps_at_max_days_on_easy():
    # 30000 * 2.5 * 1.3 = 97500, must clamp to INTERVAL_MAX_DAYS.
    result = calculate_next_state("review", 2.5, 30000, 10, "easy")
    assert result["interval_days"] == INTERVAL_MAX_DAYS


def test_interval_clamps_at_max_days_on_good():
    # 20000 * 2.5 = 50000, must clamp.
    result = calculate_next_state("review", 2.5, 20000, 10, "good")
    assert result["interval_days"] == INTERVAL_MAX_DAYS


def test_interval_at_ceiling_with_easy_stays_at_ceiling():
    # Already at the cap; another 'easy' must not exceed it.
    result = calculate_next_state("review", 2.5, INTERVAL_MAX_DAYS, 10, "easy")
    assert result["interval_days"] == INTERVAL_MAX_DAYS


# --- 10) Long-chain progression sanity check -------------------------------


def test_repeated_good_grows_interval_monotonically_until_cap():
    # Realistic SRS lifecycle: a card kept on 'good' should produce a
    # non-decreasing interval sequence and eventually hit the cap.
    state, ef, interval, reps = "new", 2.5, 0, 0
    last = -1
    for _ in range(50):
        result = calculate_next_state(state, ef, interval, reps, "good")
        assert result["interval_days"] >= last
        state = result["state"]
        ef = result["ease_factor"]
        interval = result["interval_days"]
        reps = result["repetitions"]
        last = interval
    assert interval == INTERVAL_MAX_DAYS
