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

# An application in one of these is done; every other stage counts as active.
FINISHED_STAGES = (Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN)


class MoveKind(TextChoices):
    NEXT = "next"
    SKIP = "skip"
    BACK = "back"
    REJECT = "reject"
    WITHDRAW = "withdraw"
    REOPEN = "reopen"


class Move(NamedTuple):
    target: Stage
    kind: MoveKind


def allowed_moves(stage, reopen_to=None):
    """Every move an application in ``stage`` may make, in display order.

    ``reopen_to`` is the stage held just before Rejected or Withdrawn, taken from
    the application's history; it is the only way out of those two stages.
    """
    if stage in (Stage.REJECTED, Stage.WITHDRAWN):
        return [Move(Stage(reopen_to), MoveKind.REOPEN)] if reopen_to else []
    if stage == Stage.HIRED:
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


def allowed_targets(stage, reopen_to=None):
    """The stages an application in ``stage`` may move to."""
    return frozenset(move.target for move in allowed_moves(stage, reopen_to))
