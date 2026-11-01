# Plan: Applicant Tracking System

> Source PRD: `prd/applicant-tracking-system.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Stack**: Python, Django, SQLite, uv; Tailwind CSS + DaisyUI via django-tailwind-cli; HTMX for partial updates; Ruff; pytest + pytest-django configured in `pyproject.toml`.
- **Project / app**: the project configuration package is `config`. One app, `hiring`, owns all domain code: one models module, one forms module, and a pure stage-rules module with no database code. Views and tests are split by area (candidates, jobs, skills, pipeline, dashboard, plus stage rules for tests).
- **Templates**: shared templates (base layout, sidebar, toast area) live at the project level. App templates live in `hiring`, with HTMX fragments in a dedicated `partials` folder.
- **URLs** (all namespaced under `hiring`, identified by integer pk, no slugs):
  - `/` — dashboard
  - `/accounts/login/`, `/accounts/logout/` (POST) — Django auth views; login redirects to the dashboard
  - `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`, `/candidates/<pk>/archive/` (POST), `/candidates/<pk>/unarchive/` (POST)
  - `/jobs/`, `/jobs/new/`, `/jobs/<pk>/` (job page = pipeline), `/jobs/<pk>/edit/`, `/jobs/<pk>/close/` (POST), `/jobs/<pk>/reopen/` (POST), `/jobs/<pk>/applications/new/`
  - The selected applicant is the `?application=<pk>` query parameter on the job page
  - `/applications/<pk>/panel/` — HTMX detail-panel fragment; `/applications/<pk>/move/` (POST) — stage move
  - `/skills/`, `/skills/new/`, `/skills/<pk>/edit/`
  - `/admin/` — Django admin, only for staff user management
- **Models** (all in `hiring`):
  - `Skill` — name, unique case-insensitively (database constraint)
  - `Candidate` — first/last name, email (unique case-insensitively, database constraint), phone, source (Website / Job Board / Referral / Other), source details, resume URL, archived flag; `archive()` / `unarchive()`
  - `JobOpening` — title, department, location, employment type (Full-time / Part-time / Contract / Internship), description, M2M to `Skill`, status (Open / Closed, default Open), closed-at, created/updated; `close()` / `reopen()`
  - `Application` — FK to `Candidate` and `JobOpening` (both PROTECT), unique (candidate, job), stage (default Applied), notes, created/updated; `move_to(new_stage, user)`
  - `StageChange` — FK to `Application`, from stage, to stage, `changed_by` FK to `User` (PROTECT), timestamp
- **Stages**: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn. The choices and transition rules live in the pure stage-rules module.
- **Single entry points**: every state change goes through one model method (`move_to()`, `close()`/`reopen()`, `archive()`/`unarchive()`). Views stay thin.
- **Auth**: Django's built-in User model, one staff user type, login required on every view. No roles or object-level permissions. App models are not registered in admin.
- **Deletion**: no delete actions in the app; PROTECT foreign keys guard history.
- **Feedback**: Django messages rendered as DaisyUI toasts that fade out. Full pages render them from the base layout; HTMX responses include the toast area as an out-of-band swap. Form errors are shown inline next to their fields.

---

## Phase 1: Project skeleton, authentication and app shell

**User stories**: 1, 2, 3, 4, 5, 7, 8, 9, 78

### What to build

A runnable Django project (`config` + `hiring`) managed with uv, with Tailwind/DaisyUI, HTMX, Ruff and pytest wired up. Staff log in with username and password and land on a placeholder dashboard. Every page requires login. The base layout has a sidebar with Dashboard, Candidates, Job openings and Skills links, the logged-in user, and a POST logout button. A toast area shows Django messages and fades them out. Staff accounts are managed only in Django admin.

### Acceptance criteria

- [ ] `uv` installs dependencies; the dev server and Tailwind build both run
- [ ] Ruff and pytest run from `pyproject.toml` configuration
- [ ] Anonymous requests to the dashboard redirect to login; after login the user lands on the dashboard
- [ ] Logout is a POST form in the sidebar and ends the session
- [ ] The sidebar shows the four main links and the current user
- [ ] A message added in a view appears as a toast that fades away
- [ ] Staff users can be created, deactivated and have passwords reset in Django admin; no `hiring` models appear in admin
- [ ] Shared pytest fixtures provide a logged-in staff client; a login-required test exists

---

## Phase 2: Skills

**User stories**: 39, 40, 43, 79

### What to build

The `Skill` model and a Skills area: a list page, plus create and edit pages. Skill names are unique regardless of case, enforced by a database constraint, and a duplicate shows an inline form error. The list shows how many jobs use each skill, computed in one aggregated query. Every count is zero until job openings exist.

### Acceptance criteria

- [ ] Skills can be listed, created and edited from the sidebar link
- [ ] Creating "python" when "Python" exists is refused with an error next to the name field
- [ ] The database constraint rejects case-insensitive duplicates even when form validation is bypassed
- [ ] The list shows a per-skill job count from a single aggregated query
- [ ] There is no delete action
- [ ] Tests cover the uniqueness constraint, the form error and login required

---

## Phase 3: Candidates — create, edit, detail, search and filters

**User stories**: 10, 11, 12, 13, 14, 15, 16, 17, 18, 19

### What to build

The `Candidate` model and a Candidates area. Staff can create and edit a candidate (first and last name, email, optional phone, source, optional source details, optional resume link). A detail page shows the candidate's information. Emails are unique regardless of case, enforced by a database constraint, and a duplicate shows an error next to the email field. The list page has a GET filter form: search on first name, last name or email (case-insensitive), a source filter, and Active / Archived / All (default Active). All filters stay in the query string, and there is no pagination. The Archived and All options only have data once the archive/reopen phase (Phase 9) exists.

### Acceptance criteria

- [ ] Candidates can be created, viewed and edited; the form excludes the archived flag
- [ ] Source is chosen from Website, Job Board, Referral or Other
- [ ] A second candidate with the same email, in any letter case, is refused with an inline email error, and the database constraint also enforces it
- [ ] Search matches first name, last name and email, ignoring case
- [ ] Source and status filters work; the default shows active candidates only
- [ ] Filters are kept in the URL, so a bookmarked filtered URL reproduces the list
- [ ] There is no delete action
- [ ] Tests cover the email constraint, form validation, the list filters and login required

---

## Phase 4: Job openings — create, edit, list and job page header

**User stories**: 6, 27, 28, 29, 30, 41, 42, 50, 51, 52 (Edit only)

### What to build

The `JobOpening` model with its many-to-many link to `Skill`. Staff can create and edit jobs: title, department, location, employment type, description and skills picked from the existing skills. New jobs start as Open. A basic job list page. The job page (`/jobs/<pk>/`) shows a header with the title, status, department, location, employment type, skill badges and an Edit action, plus a collapsible description. The sidebar lists every open job, linking to its job page. Renaming a skill is reflected on every job that uses it, and the Skills list counts now show real numbers.

### Acceptance criteria

- [ ] Jobs can be created and edited; the form has no status or closed-at field
- [ ] Employment type is chosen from Full-time, Part-time, Contract or Internship
- [ ] New jobs are Open
- [ ] Skills are picked from existing Skill records; renaming a skill changes it on every job page
- [ ] The job page shows the header, skill badges, the Edit action and a collapsible description
- [ ] The sidebar lists open jobs on every page
- [ ] The Skills list shows correct job counts
- [ ] There is no delete action
- [ ] Tests cover the form, the default status and login required

---

## Phase 5: Close and reopen jobs, and job list filters

**User stories**: 31, 34, 35, 36, 37, 38, 52

### What to build

`close()` and `reopen()` on `JobOpening`, exposed as POST actions from the job page header. Close asks for confirmation with an HTMX confirm prompt. Closing sets the status and records the closed-at time; reopening clears it. Both do nothing if the job is already in the target state. The header shows "Closed on [date]" for closed jobs and offers Close or Reopen as appropriate. Closed jobs drop out of the sidebar. The job list gets a GET filter form: search on title and department, and Open / Closed / All (default Open), kept in the query string.

### Acceptance criteria

- [ ] Close asks for confirmation, then marks the job Closed with a timestamp and shows a success toast
- [ ] Reopen marks the job Open and clears the timestamp
- [ ] Closing an already-closed job (or reopening an open one) changes nothing
- [ ] The header shows "Closed on [date]" and the right Close/Reopen button
- [ ] Closed jobs no longer appear in the sidebar
- [ ] Job list search and status filters work; the default is Open; filters are kept in the URL
- [ ] Tests cover close/reopen behaviour, the list filters and login required

---

## Phase 6: Applications — add from the job page, pipeline list and summary bar

**User stories**: 20, 32, 33, 44, 45, 46, 47, 48, 53, 54

### What to build

The `Application` model: PROTECT FKs to candidate and job, a unique (candidate, job) pair, a stage defaulting to Applied, and optional notes. Model validation refuses new applications to closed jobs. An "Add application" action on the job page (hidden when the job is closed) opens a form with a candidate choice and notes. The candidate choices include only active candidates who have not already applied to this job, and a stale-page duplicate is still refused. The job page gains a summary bar with one count card for each of the eight stages, and a left panel listing applicants grouped by stage with their name and days in stage. Days in stage come from the application's creation time until stage history exists. The candidate detail page gains a read-only table of the candidate's applications (job, current stage, days in stage). Closing a job leaves its applications untouched.

### Acceptance criteria

- [ ] "Add application" is shown only on open jobs and creates an application in Applied with no history row
- [ ] The candidate dropdown excludes archived candidates and candidates who have already applied to this job
- [ ] A duplicate (candidate, job) submission from a stale form is refused with a form error, and the database constraint also enforces it
- [ ] Model validation refuses an application to a closed job
- [ ] The summary bar shows counts for all eight stages, including zeros
- [ ] Applicants are grouped by stage with days in stage
- [ ] The candidate detail page lists their applications with job, stage and days in stage
- [ ] Closing a job leaves existing applications' stages unchanged
- [ ] Tests cover the constraints, closed-job validation, the form queryset and login required

---

## Phase 7: Applicant detail panel (read-only)

**User stories**: 21, 49, 55, 56, 57, 58

### What to build

Clicking an applicant in the left list loads their detail panel with HTMX, without a page reload, and pushes `?application=<pk>` onto the job page URL. A full page load with that parameter renders the applicant already selected. The panel shows the candidate's contact information and source, the current stage, a progress stepper, the read-only application notes, and a stage history timeline (from stage, to stage, who moved them, when). The timeline is empty until moves exist. Each row in the candidate page's applications table links to the job page with that application selected.

### Acceptance criteria

- [ ] Clicking an applicant swaps in the detail panel and updates the URL
- [ ] Loading `/jobs/<pk>/?application=<id>` renders that applicant selected
- [ ] An `application` parameter that doesn't belong to the job is handled safely (no panel, no error)
- [ ] The panel shows contact information, source, stage, progress stepper, notes and the history timeline
- [ ] Candidate-page application rows link to the selected applicant on the job page
- [ ] Tests cover the panel fragment response, the selected-on-load page and login required

---

## Phase 8: Stage moves

**User stories**: 59, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 73, 74, 82

### What to build

The pure stage-rules module: given a current stage, the set of allowed target stages. From an active stage an applicant can move forward to any later progress stage, except that Hired is reachable only from Offer. They can move back exactly one progress stage, or to Rejected or Withdrawn. Hired is final. The `StageChange` model, and `Application.move_to(new_stage, user)`, which checks the rules, updates the stage and writes one StageChange row in a single transaction. A same-stage move does nothing; a disallowed move raises an error. `move_to()` doesn't check job status, so moves work on closed jobs. A stage move form checks the target is allowed before the view calls `move_to()`.

The detail panel shows only the allowed moves as buttons, grouped into Move forward, Fix a mistake and Close out (none for Hired). Each move is one HTMX POST. The response returns the new detail panel plus out-of-band swaps for the grouped list, the summary bar and the toast area. A successful move shows a success toast. An invalid move (for example a stale page) returns 200 with the fresh panel, list and summary and an error toast. A same-stage move re-renders with no toast. Days in stage now come from the latest StageChange, and the history timeline fills in.

### Acceptance criteria

- [ ] The stage-rules module has no database code, and its tests run without the database
- [ ] Parametrized tests cover every from → to stage pair (Reopen is excluded and comes in Phase 9)
- [ ] `move_to()` writes exactly one StageChange with from, to, user and timestamp; a same-stage move writes none
- [ ] Disallowed moves raise an error and change nothing
- [ ] Moves work on closed jobs
- [ ] Only allowed moves appear as buttons, in the three groups; Hired shows none
- [ ] A move updates the panel, the list and the summary counts without a reload and shows a toast
- [ ] A stale or invalid move returns 200 with refreshed content and an error toast
- [ ] Days in stage reflect the latest stage change
- [ ] Tests cover the HTMX responses, including the out-of-band content and the invalid-move case

---

## Phase 9: Archive candidates and reopen applicants

**User stories**: 22, 23, 24, 25, 26, 60, 71, 72

### What to build

`Candidate.archive()` and `unarchive()`, exposed as POST actions on the candidate detail page. Archive asks for confirmation with an HTMX confirm prompt. Archiving is refused while the candidate has an active application (any stage other than Hired, Rejected or Withdrawn), with an error message listing those applications. Archiving an already-archived candidate does nothing. Archived candidates can still be edited, and are excluded from new applications (by model validation and the form's candidate choices). Their finished applications stay on pipelines with an "Archived" badge in the detail panel. The candidate list's Archived and All filters now return data.

Rejected and Withdrawn applicants show a Reopen button instead of move buttons. Reopen returns the application to the stage it held just before Rejected or Withdrawn, found from its StageChange history, through `move_to()`. Reopen is refused while the candidate is archived; this is enforced in `move_to()` and the stage move form. The panel replaces the Reopen button with a note telling staff to unarchive the candidate first.

### Acceptance criteria

- [ ] Archive asks for confirmation; it succeeds when the candidate has no active applications and is refused with a list of them otherwise
- [ ] Unarchive restores the candidate to the default (Active) list
- [ ] Archived candidates can still be edited
- [ ] Model validation and the application form both exclude archived candidates
- [ ] Archived candidates' applications show an "Archived" badge on the pipeline
- [ ] Rejected and Withdrawn applicants show only Reopen, which restores the previous stage and writes a StageChange
- [ ] Reopen for an archived candidate is refused in `move_to()` and the form; the panel shows the unarchive-first note
- [ ] Tests cover the archive block, the archived-candidate application block, Reopen's target stage and the archived Reopen refusal

---

## Phase 10: Dashboard and demo data

**User stories**: 75, 76, 77, 80, 81

### What to build

The dashboard shows the 25 most recent StageChange rows across all jobs, loaded together with their related objects in one query, with no pagination. Each entry shows the candidate, job, from stage, to stage, who moved them and when, and links to the job page with that application selected.

A management command creates demo data: several skills, three or four jobs (one closed), about twenty candidates across all sources (one archived), and applications across every stage, including rejected and withdrawn ones with history. All history goes through `move_to()`. The acting user is the first superuser, or a newly created demo user if there is none. A reset option clears the app's tables first.

### Acceptance criteria

- [ ] The dashboard lists at most 25 stage changes, newest first, with all six details
- [ ] The dashboard runs a constant number of queries regardless of row count
- [ ] Each entry links to the selected applicant on the job page
- [ ] The demo command populates every page with data covering every stage, a closed job and an archived candidate
- [ ] All demo history rows come from `move_to()`
- [ ] The reset option returns the database to a known demo state, and running it twice gives the same result
- [ ] Tests cover the dashboard contents and ordering, the query count and login required
