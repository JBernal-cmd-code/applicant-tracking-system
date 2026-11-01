"""Hiring stages. Pure rules only: nothing in this module touches the database."""

from typing import NamedTuple

from django.db.models import TextChoices


class Stage(TextChoices):
    APPLIED = "applied", "Applied"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    FINAL_REVIEW = "final_review", "Final Review"
    OFFER = "offer", "Offer"
    HIRED = "hired", "Hired"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


# The forward path an application can travel; Rejected and Withdrawn sit outside it.
PROGRESS_STAGES = (
    Stage.APPLIED,
    Stage.SCREENING,
    Stage.INTERVIEW,
    Stage.FINAL_REVIEW,
    Stage.OFFER,
    Stage.HIRED,
)


class MoveKind(TextChoices):
    NEXT = "next"
    SKIP = "skip"
    BACK = "back"
    REJECT = "reject"
    WITHDRAW = "withdraw"


class Move(NamedTuple):
    target: Stage
    kind: MoveKind


def allowed_moves(stage):
    """Every move an application in ``stage`` may make, in display order."""
    if stage not in PROGRESS_STAGES or stage == Stage.HIRED:
        # Hired is final; Rejected and Withdrawn wait for Reopen (Phase 9).
        return []
    i = PROGRESS_STAGES.index(stage)
    moves = []
    for j, target in enumerate(PROGRESS_STAGES[i + 1 :], start=i + 1):
        if target == Stage.HIRED and stage != Stage.OFFER:
            continue
        moves.append(Move(target, MoveKind.NEXT if j == i + 1 else MoveKind.SKIP))
    if i > 0:
        moves.append(Move(PROGRESS_STAGES[i - 1], MoveKind.BACK))
    moves.append(Move(Stage.REJECTED, MoveKind.REJECT))
    moves.append(Move(Stage.WITHDRAWN, MoveKind.WITHDRAW))
    return moves


def allowed_targets(stage):
    """The stages an application in ``stage`` may move to."""
    return frozenset(move.target for move in allowed_moves(stage))
