from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.db.models.functions import Coalesce, Lower
from django.utils import timezone

from hiring.stages import FINISHED_STAGES, PROGRESS_STAGES, Stage, allowed_targets


class Skill(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_ci",
                violation_error_message="A skill with this name already exists.",
            ),
        ]

    def __str__(self):
        return self.name


class Candidate(models.Model):
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        JOB_BOARD = "job_board", "Job Board"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=20, choices=Source)
    source_details = models.CharField(max_length=255, blank=True)
    resume_url = models.URLField("resume link", blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_candidate_email_ci",
                violation_error_message="A candidate with this email already exists.",
            ),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def archive(self):
        """Hide the candidate from the default list. Refused while any application is active."""
        if self.archived:
            return
        active = self.applications.exclude(stage__in=FINISHED_STAGES).select_related("job")
        if active:
            jobs = ", ".join(f"{a.job} ({a.get_stage_display()})" for a in active)
            raise ValidationError(f"Can't archive {self}: still active for {jobs}.")
        self.archived = True
        self.save(update_fields=["archived"])

    def unarchive(self):
        if not self.archived:
            return
        self.archived = False
        self.save(update_fields=["archived"])


class JobOpening(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EmploymentType)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, blank=True, related_name="job_openings")
    status = models.CharField(max_length=10, choices=Status, default=Status.OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def close(self):
        if self.status == self.Status.CLOSED:
            return
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])

    def reopen(self):
        if self.status == self.Status.OPEN:
            return
        self.status = self.Status.OPEN
        self.closed_at = None
        self.save(update_fields=["status", "closed_at", "updated_at"])


class ApplicationQuerySet(models.QuerySet):
    def with_stage_entered_at(self):
        """When each application entered its current stage: its latest change, else creation."""
        return self.annotate(
            stage_entered_at=Coalesce(Max("stage_changes__changed_at"), "created_at")
        )


class Application(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT, related_name="applications")
    job = models.ForeignKey(JobOpening, on_delete=models.PROTECT, related_name="applications")
    stage = models.CharField(max_length=20, choices=Stage, default=Stage.APPLIED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ApplicationQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_application_per_job",
                violation_error_message="This candidate has already applied to this job.",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} for {self.job}"

    def clean(self):
        # Only new applications are blocked; existing ones keep moving after a close.
        if self._state.adding and self.job_id and self.job.status == JobOpening.Status.CLOSED:
            raise ValidationError("This job is closed and isn't accepting new applications.")
        if self._state.adding and self.candidate_id and self.candidate.archived:
            raise ValidationError("This candidate is archived and can't apply to jobs.")

    def move_to(self, new_stage, user):
        """The one way to change stage. Returns the StageChange, or None for a same-stage move."""
        if new_stage == self.stage:
            return None
        if new_stage not in allowed_targets(self.stage, self.reopen_stage):
            raise ValidationError(
                f"Can't move from {self.get_stage_display()} to {Stage(new_stage).label}."
            )
        if self.reopen_blocked:
            raise ValidationError(self.REOPEN_BLOCKED_MESSAGE.format(candidate=self.candidate))
        with transaction.atomic():
            change = StageChange.objects.create(
                application=self, from_stage=self.stage, to_stage=new_stage, changed_by=user
            )
            self.stage = new_stage
            self.save(update_fields=["stage", "updated_at"])
        return change

    @property
    def reopen_stage(self):
        """For Rejected or Withdrawn, the stage held just before; otherwise None."""
        if self.stage not in (Stage.REJECTED, Stage.WITHDRAWN):
            return None
        # The latest change is the one that entered the current stage.
        latest = self.stage_changes.first()
        return latest.from_stage if latest else None

    REOPEN_BLOCKED_MESSAGE = "Unarchive {candidate} before reopening this application."

    @property
    def reopen_blocked(self):
        # Checked here, not in the pure stage rules, because it depends on candidate data.
        return self.stage in (Stage.REJECTED, Stage.WITHDRAWN) and self.candidate.archived

    @property
    def days_in_stage(self):
        # Lists annotate stage_entered_at (see with_stage_entered_at) to avoid a query per row.
        entered = getattr(self, "stage_entered_at", None)
        if entered is None:
            latest = self.stage_changes.first()
            entered = latest.changed_at if latest else self.created_at
        return (timezone.now() - entered).days

    @property
    def progress_steps(self):
        # Rejected and Withdrawn show how far the application got before it ended.
        stages = list(PROGRESS_STAGES)
        current = self.reopen_stage or self.stage
        reached = stages.index(current) if current in stages else -1
        return [{"label": stage.label, "reached": i <= reached} for i, stage in enumerate(stages)]


class StageChange(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.PROTECT, related_name="stage_changes"
    )
    from_stage = models.CharField(max_length=20, choices=Stage)
    to_stage = models.CharField(max_length=20, choices=Stage)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at", "-pk"]

    def __str__(self):
        return f"{self.application}: {self.from_stage} → {self.to_stage}"
