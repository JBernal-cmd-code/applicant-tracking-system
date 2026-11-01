# Applicant Tracking System

Internal Django web app for logged-in hiring staff to track candidates, job openings, and each application's progress through the hiring stages.

## Stack

- Python, Django, SQLite; **uv** is the package manager.
- Tailwind CSS + DaisyUI via django-tailwind-cli; HTMX for partial page updates.
- Ruff for formatting and linting; pytest + pytest-django, configured in `pyproject.toml`.

## Commands

- Install and set up: `uv sync`, then `uv run python manage.py migrate`
- Dev server with Tailwind watcher: `uv run python manage.py tailwind runserver`
- Tests: `uv run pytest`
- Lint and format: `uv run ruff check .` and `uv run ruff format .`

## Architecture decisions

- The `hiring` app owns all domain code, with views and tests split into modules by area; `config` is the project package. Stage choices and transition rules live in a pure stage-rules module with no database code.
- Every state change goes through a single model method (`move_to()`, `close()`/`reopen()`, `archive()`/`unarchive()`). Views stay thin.
- No delete actions in the app; protected foreign keys guard hiring history.
- Django's built-in auth and User model, one staff user type, login required on every view, no roles or object-level permissions.
- App models are not registered in Django admin; admin is only for managing staff accounts.
- Action feedback uses Django messages shown as DaisyUI toasts; HTMX responses update the toast area with an out-of-band swap.
- HTMX partials live in `hiring/templates/hiring/partials/`; pipeline responses swap the detail panel and update the list, summary bar and toasts with out-of-band swaps.
- Stage rules live in `hiring/stages.py`; stage changes only go through `Application.move_to()`, never by setting `stage` directly.
- Test helpers (`make_application(stage=...)` in `hiring/tests/conftest.py`) reach later stages through `move_to()`, so history exists.

## References

- PRD (requirements, models, rules, scope): `prd/applicant-tracking-system.md`
- Implementation plan (phases, acceptance criteria): `plans/applicant-tracking-system.md`
- Prototypes (reference only, not production code): `prototypes/`

