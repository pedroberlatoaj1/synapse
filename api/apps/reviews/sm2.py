"""Pure SM-2 mathematical engine — domain core, no ORM, no clock.

Variante Synapse: a 4-rating SM-2 (again / hard / good / easy) with
explicit boundaries on `ease_factor` and `interval_days`. The module is
intentionally infrastructure-free: every input becomes a deterministic
output, which lets the API layer (Bloco 8) compose this with `now()`
and the ORM, while the engine itself stays sub-millisecond unit-testable
without a database, freezegun, or any Django context.

Boundaries
----------
EASE_FACTOR_MIN = 1.30
    Hard floor on the ease factor. Without it, repeated `again` ratings
    would drive ef toward zero, and any subsequent `good` would compute
    `interval = old_interval * 0` = 0, trapping the card in "due now"
    forever. 1.30 is the canonical Anki/SM-2 lower bound.

INTERVAL_MAX_DAYS = 36500
    ~100-year ceiling on the next interval. Prevents a runaway chain of
    `easy` ratings from overflowing `due_at = now + timedelta(days=...)`
    against `datetime.max`, and also caps the practically useful range
    of an SRS schedule at one human lifetime.

INTERVAL_MIN_AFTER_SUCCESS = 1
    Any non-`again` rating yields at least a 1-day interval. Protects
    against `round(0 * x) == 0` for new/lapsed cards (interval_days=0):
    without this floor, a `hard` on a fresh card would compute interval
    = 0 and the card would re-appear immediately, defeating SRS.

State machine for successful ratings (hard / good / easy)
----------------------------------------------------------
The spec defines explicit state changes only for the `again` branch
("lapsed if was review, else learning"). For successful ratings, the
engine uses the simplest sensible promotion ladder, where every success
moves the card one rung closer to long-term stability:

    new      -> learning
    learning -> review     (graduates on first success)
    review   -> review     (stays mature)
    lapsed   -> review     (recovered after relearning)

This keeps the state graph small, monotonic on success, and cheap to
reason about. A future variant (e.g. requiring N successes to graduate)
would only need to change `_next_state_on_success`.

Return shape
------------
The function returns a dict with `{state, ease_factor, interval_days,
repetitions}` — mirroring the inputs minus `rating`. `due_at` is
intentionally NOT in the output: composing it requires `now()`, which
would make the engine impure and harder to unit-test. The caller
(POST /reviews handler) computes `due_at = now() + timedelta(days=
result["interval_days"])` and persists.

Rounding
--------
Interval is computed as a real-valued multiplication then `round()`-ed
to int. Python 3's `round` is banker's rounding (half-to-even, e.g.
round(2.5) == 2, round(3.5) == 4). The half-tie is rare in practice
and a 1-day differential sits below the SRS noise floor, so we accept
it rather than introducing a custom rounding shim. The post-round value
is then clamped to [INTERVAL_MIN_AFTER_SUCCESS, INTERVAL_MAX_DAYS] for
successful ratings, or set to 0 for `again`.
"""
from __future__ import annotations

EASE_FACTOR_MIN: float = 1.30
INTERVAL_MAX_DAYS: int = 36500
INTERVAL_MIN_AFTER_SUCCESS: int = 1

VALID_STATES: frozenset[str] = frozenset({"new", "learning", "review", "lapsed"})
VALID_RATINGS: frozenset[str] = frozenset({"again", "hard", "good", "easy"})

_SUCCESS_TRANSITIONS: dict[str, str] = {
    "new": "learning",
    "learning": "review",
    "review": "review",
    "lapsed": "review",
}


def calculate_next_state(
    state: str,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    rating: str,
) -> dict:
    """Compute the next SM-2 state for a single review evaluation.

    The algorithm runs in three logical steps:

    1. **Validate** — `state` and `rating` are checked against the
       allowed sets. Anything else raises ``ValueError`` so an invalid
       payload from upstream surfaces immediately rather than producing
       a silently-wrong card.

    2. **Branch on rating** — derive the new ``ease_factor`` and
       ``interval_days``:

       - ``again``: full reset. ``repetitions = 0``, ``interval_days =
         0``, and ``ease_factor`` is multiplied by 0.85 (clamped at
         ``EASE_FACTOR_MIN``). State becomes ``"lapsed"`` if the card
         was already in ``"review"``, otherwise ``"learning"``.
       - ``hard``: ``interval_days = max(1, round(interval_days *
         1.2))``; ``ease_factor`` is reduced by 0.15 (clamped at
         ``EASE_FACTOR_MIN``).
       - ``good``: ``interval_days = max(1, round(interval_days *
         ease_factor))``; ``ease_factor`` unchanged.
       - ``easy``: ``interval_days = max(1, round(interval_days *
         ease_factor * 1.3))``; ``ease_factor += 0.15`` (no upper
         clamp — large ef is harmless because the interval cap takes
         over).

       After computation, ``interval_days`` is clamped to at most
       ``INTERVAL_MAX_DAYS`` for non-``again`` ratings.

    3. **Resolve next state** — for successful ratings, look up the
       next state from the promotion ladder defined in
       ``_SUCCESS_TRANSITIONS``. Repetitions are incremented by 1.

    Args:
        state: Current card lifecycle state. One of ``"new"``,
            ``"learning"``, ``"review"``, ``"lapsed"``.
        ease_factor: Current ease factor. Expected ``>= 1.30``; if a
            caller passes a smaller value the result is still re-clamped
            at the floor.
        interval_days: Current scheduled interval in days. Expected
            ``>= 0``.
        repetitions: Counter of consecutive successful reviews. Reset
            to 0 on ``again``, otherwise incremented by 1.
        rating: User's evaluation. One of ``"again"``, ``"hard"``,
            ``"good"``, ``"easy"``.

    Returns:
        A dict with the keys ``{"state", "ease_factor",
        "interval_days", "repetitions"}``. The caller is responsible
        for deriving ``due_at`` from a real-time clock.

    Raises:
        ValueError: If ``state`` is not in :data:`VALID_STATES` or
            ``rating`` is not in :data:`VALID_RATINGS`.
    """
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state: {state!r}")
    if rating not in VALID_RATINGS:
        raise ValueError(f"Invalid rating: {rating!r}")

    if rating == "again":
        new_ease = max(EASE_FACTOR_MIN, ease_factor * 0.85)
        return {
            "state": "lapsed" if state == "review" else "learning",
            "ease_factor": new_ease,
            "interval_days": 0,
            "repetitions": 0,
        }

    # --- Successful path: hard / good / easy --------------------------------
    if rating == "hard":
        new_interval = max(INTERVAL_MIN_AFTER_SUCCESS, round(interval_days * 1.2))
        new_ease = max(EASE_FACTOR_MIN, ease_factor - 0.15)
    elif rating == "good":
        new_interval = max(
            INTERVAL_MIN_AFTER_SUCCESS, round(interval_days * ease_factor)
        )
        new_ease = ease_factor
    else:  # rating == "easy"
        new_interval = max(
            INTERVAL_MIN_AFTER_SUCCESS, round(interval_days * ease_factor * 1.3)
        )
        new_ease = ease_factor + 0.15

    new_interval = min(new_interval, INTERVAL_MAX_DAYS)

    return {
        "state": _SUCCESS_TRANSITIONS[state],
        "ease_factor": new_ease,
        "interval_days": new_interval,
        "repetitions": repetitions + 1,
    }
