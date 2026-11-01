# Applicant Tracking System

## Project Overview

This is a new Django application named **Applicant Tracking System (ATS)**.

This app is used by hiring staff, such as recruiters and hiring managers, so they can keep track of job openings and candidates, and see and move applicants through the hiring stages.

There is no existing code yet. This repository starts from scratch.

## Technology Stack

The project must use:

- Python
- Django
- SQLite
- `uv` for package and dependency management
- Tailwind CSS with DaisyUI using `django-tailwind-cli`
- HTMX
- Ruff for formatting and linting
- pytest for automated tests

## Business Requirements

The hiring department has provided the following requirements:

1. **This is an internal hiring system.** It will be used by employees involved in the hiring process. Candidates will not log in to the system.
2. **Staff need to keep track of candidates and their basic information.** Candidates may come from the company website, job boards, referrals, or other outside sources.
3. **Staff need to create and edit job openings.** A job opening can be open or closed.
4. **Staff need to record when a candidate applies for a job opening.** A candidate may apply for several different jobs, but should not have more than one application for the same opening.
5. **Applications move through a defined hiring process.** The system must include these stages: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, and Withdrawn.
6. **Staff need an easy way to see where applicants are in the hiring process and move them from one stage to another.** Moving an applicant should not require reloading the entire page.
7. **The system needs to keep track of the skills associated with each job opening.** The same skill may apply to many different openings.
8. **We need to decide how candidate records should be managed over time.** For example, we have not decided when a candidate should be edited, archived, deactivated, or removed.
9. **We need to decide what happens when a job opening closes.** Existing applications may still be in progress, and an opening may or may not be allowed to reopen.

## Prototypes

During this interview I will pause twice to use `/prototype`:

1. **Application state prototype**: when we reach the rules for how applications move between hiring stages.
2. **UI prototype**: when we reach the design of the hiring pipeline/dashboard for viewing and moving applications.

Please flag when a question is about either of these so I can pause and prototype.
