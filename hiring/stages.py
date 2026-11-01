"""Hiring stages. Pure rules only: nothing in this module touches the database."""

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
