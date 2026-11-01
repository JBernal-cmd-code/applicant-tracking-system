"""Stage rules. These tests use no database."""

import itertools

import pytest

from hiring.stages import MoveKind, Stage, allowed_moves, allowed_targets

S = Stage

# Spelled out by hand so the test doesn't share logic with the rules it checks.
ALLOWED = {
    S.APPLIED: {S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.SCREENING: {S.APPLIED, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.INTERVIEW: {S.SCREENING, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.FINAL_REVIEW: {S.INTERVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.OFFER: {S.FINAL_REVIEW, S.HIRED, S.REJECTED, S.WITHDRAWN},
    S.HIRED: set(),
    # Without history there is nowhere to reopen to; Reopen is covered below.
    S.REJECTED: set(),
    S.WITHDRAWN: set(),
}

ACTIVE = [S.APPLIED, S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER]


@pytest.mark.parametrize(("current", "target"), list(itertools.product(Stage, Stage)))
def test_every_stage_pair(current, target):
    expected = target in ALLOWED[current]

    assert (target in allowed_targets(current)) is expected


@pytest.mark.parametrize(
    ("closed_as", "previous"), list(itertools.product([S.REJECTED, S.WITHDRAWN], ACTIVE))
)
def test_rejected_and_withdrawn_allow_only_reopen_to_previous_stage(closed_as, previous):
    assert allowed_moves(closed_as, reopen_to=previous) == [(previous, MoveKind.REOPEN)]


@pytest.mark.parametrize("stage", [*ACTIVE, S.HIRED])
def test_reopen_stage_is_ignored_outside_rejected_and_withdrawn(stage):
    assert allowed_targets(stage, reopen_to=S.APPLIED) == allowed_targets(stage)
