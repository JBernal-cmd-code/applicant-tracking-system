from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from hiring.models import Application, Candidate, JobOpening, Skill, StageChange
from hiring.stages import Stage

SKILLS = [
    "Python",
    "Django",
    "SQL",
    "JavaScript",
    "React",
    "Figma",
    "Data Analysis",
    "Project Management",
    "Communication",
]

Type = JobOpening.EmploymentType

# (title, department, location, employment type, description, skills, closed days ago or None)
JOBS = [
    (
        "Backend Developer",
        "Engineering",
        "Remote",
        Type.FULL_TIME,
        "Build and maintain the Django services behind our customer portal.",
        ["Python", "Django", "SQL"],
        None,
    ),
    (
        "Frontend Developer",
        "Engineering",
        "Austin, TX",
        Type.FULL_TIME,
        "Own the React front end and work closely with design on new features.",
        ["JavaScript", "React", "Figma"],
        None,
    ),
    (
        "Data Analyst Intern",
        "Analytics",
        "Dallas, TX",
        Type.INTERNSHIP,
        "Summer internship turning raw sales data into weekly reports.",
        ["SQL", "Python", "Data Analysis"],
        None,
    ),
    (
        "Project Coordinator",
        "Operations",
        "Amarillo, TX",
        Type.CONTRACT,
        "Six-month contract coordinating the office move and vendor schedules.",
        ["Project Management", "Communication"],
        4,
    ),
]

Source = Candidate.Source

# (first name, last name, source, source details)
CANDIDATES = [
    ("Maria", "Garcia", Source.WEBSITE, ""),
    ("James", "Smith", Source.JOB_BOARD, "Indeed"),
    ("Aisha", "Khan", Source.REFERRAL, "Referred by Tom in Engineering"),
    ("Wei", "Chen", Source.JOB_BOARD, "LinkedIn"),
    ("Olivia", "Brown", Source.WEBSITE, ""),
    ("Diego", "Hernandez", Source.OTHER, "Met at the WTAMU career fair"),
    ("Priya", "Patel", Source.REFERRAL, "Referred by Dana in Analytics"),
    ("Noah", "Johnson", Source.WEBSITE, ""),
    ("Fatima", "Ali", Source.JOB_BOARD, "Indeed"),
    ("Liam", "Williams", Source.OTHER, "Austin tech meetup"),
    ("Sofia", "Martinez", Source.WEBSITE, ""),
    ("Kenji", "Tanaka", Source.REFERRAL, "Referred by Sam in Operations"),
    ("Emma", "Davis", Source.JOB_BOARD, "LinkedIn"),
    ("Mateo", "Lopez", Source.WEBSITE, ""),
    ("Grace", "Kim", Source.OTHER, "Cold email"),
    ("Ethan", "Wilson", Source.JOB_BOARD, "Indeed"),
    ("Hannah", "Nguyen", Source.WEBSITE, ""),
    ("Lucas", "Moore", Source.REFERRAL, "Referred by Priya on the data team"),
    ("Chloe", "Taylor", Source.WEBSITE, ""),
    ("Samuel", "Okafor", Source.JOB_BOARD, "LinkedIn"),
]

# Archived after its applications are finished, so archive() accepts it.
ARCHIVED_CANDIDATE = "Liam"

S = Stage

# (candidate first name, job title, days ago applied, stages moved through, notes)
APPLICATIONS = [
    ("Maria", "Backend Developer", 2, [], "Strong Django portfolio on GitHub."),
    ("James", "Backend Developer", 12, [S.SCREENING], ""),
    ("Aisha", "Backend Developer", 20, [S.SCREENING, S.INTERVIEW], "Referral, fast-track."),
    ("Wei", "Backend Developer", 30, [S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW], ""),
    (
        "Olivia",
        "Backend Developer",
        25,
        [S.INTERVIEW, S.SCREENING],
        "Moved back to redo screening.",
    ),
    ("Diego", "Backend Developer", 15, [S.REJECTED], "Missing required SQL experience."),
    ("Noah", "Frontend Developer", 3, [], ""),
    ("Fatima", "Frontend Developer", 18, [S.SCREENING, S.INTERVIEW], ""),
    ("Sofia", "Frontend Developer", 35, [S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER], ""),
    ("Kenji", "Frontend Developer", 22, [S.SCREENING, S.WITHDRAWN], "Accepted another offer."),
    ("Wei", "Frontend Developer", 10, [S.SCREENING, S.REJECTED], ""),
    ("Priya", "Data Analyst Intern", 14, [S.SCREENING, S.WITHDRAWN, S.SCREENING, S.INTERVIEW], ""),
    ("Emma", "Data Analyst Intern", 6, [S.SCREENING], ""),
    ("Mateo", "Data Analyst Intern", 1, [], "Applied through the website form."),
    ("Grace", "Data Analyst Intern", 16, [S.INTERVIEW, S.REJECTED], ""),
    ("Hannah", "Project Coordinator", 40, [S.SCREENING, S.INTERVIEW, S.OFFER, S.HIRED], ""),
    ("Ethan", "Project Coordinator", 38, [S.SCREENING, S.INTERVIEW, S.FINAL_REVIEW, S.OFFER], ""),
    ("Lucas", "Project Coordinator", 33, [S.SCREENING, S.REJECTED], ""),
    ("Liam", "Project Coordinator", 36, [S.SCREENING, S.INTERVIEW, S.REJECTED], ""),
    ("Chloe", "Project Coordinator", 28, [S.WITHDRAWN], "Relocating out of state."),
    ("Samuel", "Project Coordinator", 30, [S.SCREENING], ""),
]


class Command(BaseCommand):
    help = "Create demo skills, jobs, candidates and applications with stage history."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Delete all hiring data before seeding."
        )

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        if reset:
            self.clear()
        elif Skill.objects.exists() or Candidate.objects.exists() or JobOpening.objects.exists():
            raise CommandError("Hiring data already exists. Run with --reset to replace it.")

        user = self.acting_user()
        now = timezone.now()

        skills = {name: Skill.objects.create(name=name) for name in SKILLS}

        jobs = {}
        for title, department, location, kind, description, skill_names, _ in JOBS:
            job = JobOpening.objects.create(
                title=title,
                department=department,
                location=location,
                employment_type=kind,
                description=description,
            )
            job.skills.set(skills[name] for name in skill_names)
            jobs[title] = job

        candidates = {}
        for first, last, source, details in CANDIDATES:
            candidates[first] = Candidate.objects.create(
                first_name=first,
                last_name=last,
                email=f"{first}.{last}@example.com".lower(),
                phone=f"806-555-{len(candidates):04d}",
                source=source,
                source_details=details,
            )

        for first, title, days_ago, path, notes in APPLICATIONS:
            application = Application(candidate=candidates[first], job=jobs[title], notes=notes)
            application.full_clean()
            application.save()
            # Spread the history over the days since applying so days-in-stage looks lifelike.
            applied_at = now - timedelta(days=days_ago)
            Application.objects.filter(pk=application.pk).update(created_at=applied_at)
            step = timedelta(days=days_ago) / (len(path) + 1)
            for i, stage in enumerate(path, start=1):
                change = application.move_to(stage, user)
                StageChange.objects.filter(pk=change.pk).update(changed_at=applied_at + step * i)

        # Close jobs and archive candidates last: both refuse new applications.
        for title, *_, closed_days_ago in JOBS:
            if closed_days_ago is not None:
                jobs[title].close()
                JobOpening.objects.filter(pk=jobs[title].pk).update(
                    closed_at=now - timedelta(days=closed_days_ago)
                )
        candidates[ARCHIVED_CANDIDATE].archive()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(SKILLS)} skills, {len(JOBS)} jobs, {len(CANDIDATES)} candidates "
                f"and {len(APPLICATIONS)} applications, with history by {user.get_username()}."
            )
        )

    def clear(self):
        # Children first: protected foreign keys refuse to delete parents with history.
        StageChange.objects.all().delete()
        Application.objects.all().delete()
        Candidate.objects.all().delete()
        JobOpening.objects.all().delete()
        Skill.objects.all().delete()

    def acting_user(self):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).order_by("pk").first()
        if user:
            return user
        user, created = User.objects.get_or_create(username="demo")
        if created:
            user.set_unusable_password()
            user.save()
            self.stdout.write("No superuser found; history is attributed to a new 'demo' user.")
        return user
