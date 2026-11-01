"""Stage rules. These tests use no database."""

import itertools

import pytest

from hiring.stages import Stage, allowed_targets

S = Stage

# Spelled out by hand so the test doesn't share logic with the rules it checks.
ALLOWED = {
    S.APPLIED: {S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.SCREENING: {S.APPLIED, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.INTERVIEW: {S.SCREENING, S.FINAL_REVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.FINAL_REVIEW: {S.INTERVIEW, S.OFFER, S.REJECTED, S.WITHDRAWN},
    S.OFFER: {S.FINAL_REVIEW, S.HIRED, S.REJECTED, S.WITHDRAWN},
    S.HIRED: set(),
    # Reopen, the only way out of Rejected and Withdrawn, arrives in Phase 9.
    S.REJECTED: set(),
    S.WITHDRAWN: set(),
}


@pytest.mark.parametrize(("current", "target"), list(itertools.product(Stage, Stage)))
def test_every_stage_pair(current, target):
    expected = target in ALLOWED[current]

    assert (target in allowed_targets(current)) is expected
