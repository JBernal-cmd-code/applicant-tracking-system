# PRD: Applicant Tracking System

## Problem Statement

The hiring department (recruiters, hiring managers and other staff involved in hiring) has no shared system for tracking job openings and the people applying to them. Candidates arrive from the company website, job boards, referrals and other sources, and staff need one place to record who they are, which openings they applied to, and where each application stands in the hiring process.

Without a system:

- The same person can be recorded twice, and nobody can be sure a candidate hasn't already applied to an opening.
- There is no reliable view of where each applicant is in the hiring stages, and moving someone forward means updating spreadsheets or notes by hand.
- Nobody can see *how* an applicant got to their current stage, who moved them, or when.
- There are no agreed rules for what happens to candidate records over time or to in-progress applications when an opening closes.

## Solution

An internal Django web application, used only by logged-in staff (candidates never log in), that lets staff:

- Maintain a single, de-duplicated record for each candidate (unique email), including where they came from, and archive candidates who are no longer active instead of deleting them.
- Create and edit job openings, tag them with shared skills, and close and reopen them.
- Record a candidate's application to an opening, with at most one application per candidate per opening.
- Work each job's pipeline on a single page: see counts per stage, browse applicants grouped by stage, select one to see their details and full stage history, and move them between stages with buttons that only offer moves the hiring rules allow. Moves happen without reloading the page.
- See a dashboard of recent stage changes across all jobs as soon as they log in.

The hiring stages are Applied, Screening, Interview, Final Review, Offer, Hired, Rejected and Withdrawn. Every stage change goes through one rule-enforcing operation and is recorded in a history log.

## User Stories

### Access and navigation

1. As a staff member, I want to log in with a username and password, so that only employees can see hiring data.
2. As a staff member, I want every page to require login, so that candidate information is never exposed to someone who isn't signed in.
3. As a staff member, I want to land on the dashboard after logging in, so that I immediately see what has changed recently.
4. As a staff member, I want to log out from a button in the sidebar, so that I can end my session on a shared computer.
5. As a staff member, I want a sidebar with links to Dashboard, Candidates, Job openings and Skills, so that I can move between the main areas quickly.
6. As a staff member, I want the sidebar to list every open job, so that I can jump straight into a job's pipeline.
7. As an administrator, I want to create staff accounts in Django admin, so that new hiring staff can get access.
8. As an administrator, I want to deactivate a departing staff member's account rather than delete it, so that the stage history they recorded keeps its author.
9. As an administrator, I want to reset a staff member's password in Django admin, so that locked-out staff can regain access without an email reset flow.

### Candidates

10. As a staff member, I want to add a candidate with first name, last name, email, optional phone, source, optional source details and an optional resume link, so that I have their basic information in one place.
11. As a staff member, I want to choose the candidate's source from Website, Job Board, Referral or Other, so that we know where candidates come from.
12. As a staff member, I want an optional free-text source details field, so that I can note who referred someone or which event we met them at.
13. As a staff member, I want the system to refuse a second candidate with the same email, regardless of letter case, so that one person never has two records.
14. As a staff member, I want to see a clear error next to the email field when the email already exists, so that I know to find the existing record instead.
15. As a staff member, I want to edit a candidate's details at any time, including archived candidates, so that contact information stays current.
16. As a staff member, I want to search candidates by first name, last name or email, so that I can find a person quickly.
17. As a staff member, I want to filter candidates by source, so that I can see, for example, all referrals.
18. As a staff member, I want the candidates list to show active candidates by default, with options for Archived and All, so that inactive people don't clutter my daily view.
19. As a staff member, I want my search and filters to be kept in the page URL, so that I can bookmark or share a filtered list.
20. As a staff member, I want a candidate detail page showing their information and a list of every application they have (job, current stage, days in stage), so that I can see the whole person at a glance.
21. As a staff member, I want each application on the candidate page to link to that applicant on the job's pipeline, so that I can go straight to where moves happen.
22. As a staff member, I want to archive a candidate, after a confirmation prompt, so that people no longer in consideration are hidden from the default list without losing their history.
23. As a staff member, I want archiving to be refused while a candidate has an active application, with a message listing those applications, so that someone mid-process never disappears from view.
24. As a staff member, I want to unarchive a candidate, so that a returning candidate can be considered again.
25. As a staff member, I want archived candidates to be excluded from new applications, so that inactive people aren't accidentally put back into a pipeline.
26. As a staff member, I want archived candidates' finished applications to remain visible on pipelines with an "Archived" badge, so that the hiring record for each job stays complete.

### Job openings

27. As a staff member, I want to create a job opening with title, department, location, employment type, description and skills, so that the opening is described clearly.
28. As a staff member, I want to choose the employment type from Full-time, Part-time, Contract or Internship, so that openings are labelled consistently.
29. As a staff member, I want new job openings to start as Open, so that they are ready for applications immediately.
30. As a staff member, I want to edit a job's details and skills, so that I can correct or update the posting.
31. As a staff member, I want to close a job with a dedicated Close button and a confirmation prompt, so that I don't close one by accident.
32. As a staff member, I want closing a job to leave existing applications exactly where they are, so that I can still finish offers and reject the remaining applicants.
33. As a staff member, I want a closed job to refuse new applications, so that "closed" really means no new applicants.
34. As a staff member, I want to reopen a closed job, so that an opening closed too early or a hire that fell through can be handled.
35. As a staff member, I want the system to record when a job was closed and to show "Closed on [date]", so that I know how long it has been closed.
36. As a staff member, I want to search job openings by title or department, so that I can find a specific opening.
37. As a staff member, I want the job openings list to show open jobs by default, with options for Closed and All, so that my daily view shows active hiring.
38. As a staff member, I want my job search and filters kept in the page URL, so that I can bookmark a filtered list.

### Skills

39. As a staff member, I want a Skills page where I can list, add and edit skills, so that the skill vocabulary is managed in one place.
40. As a staff member, I want skill names to be unique regardless of letter case, so that "Python" and "python" can't both exist.
41. As a staff member, I want to pick a job's skills from the existing skills list, so that jobs share the same skill records.
42. As a staff member, I want renaming a skill to update it on every job that uses it, so that fixing a typo fixes it everywhere.
43. As a staff member, I want the skills list to show how many jobs use each skill, so that I can see which skills matter most and which are unused.

### Applications

44. As a staff member, I want to add an application from a job's page by choosing an existing candidate and optionally entering notes, so that I can record that someone applied.
45. As a staff member, I want the candidate choices to include only active candidates who haven't already applied to this job, so that I can't pick an invalid option.
46. As a staff member, I want the system to refuse a second application from the same candidate to the same job, even from a stale page, so that the one-application rule always holds.
47. As a staff member, I want the "Add application" button hidden on closed jobs, so that I'm not offered something the system won't allow.
48. As a staff member, I want every new application to start in Applied, so that all applicants enter the process the same way.
49. As a staff member, I want the notes entered when adding an application to be shown read-only on the applicant's detail panel, so that context from the start of the process stays visible.

### Pipeline (job page)

50. As a staff member, I want a job's page to be its pipeline, with the job's title, status, department, location, type and skills in the header, so that I have job context while working applicants.
51. As a staff member, I want the job description in a collapsible section, so that long descriptions don't push the pipeline down.
52. As a staff member, I want Edit, Close or Reopen, and Add application actions in the job header, so that everything about a job is managed from one page.
53. As a staff member, I want a summary bar with a count card for each of the eight stages, so that I can see the shape of the pipeline at a glance.
54. As a staff member, I want a list of the job's applicants grouped by stage, each showing days in their current stage, so that I can spot people who have been waiting too long.
55. As a staff member, I want to click an applicant to open their detail panel without reloading the page, so that reviewing applicants is quick.
56. As a staff member, I want the selected applicant reflected in the page URL, so that refreshing or bookmarking brings me back to the same applicant.
57. As a staff member, I want the detail panel to show the applicant's contact information, source, current stage and a progress stepper, so that I understand where they are.
58. As a staff member, I want the detail panel to show the full stage history (from stage, to stage, who moved them, when), so that I know how they got here.
59. As a staff member, I want the move buttons grouped into Move forward, Fix a mistake and Close out, so that the purpose of each move is clear.
60. As a staff member, I want rejected or withdrawn applicants to show a Reopen button instead of move buttons, so that the only way back is an explicit reopen.
61. As a staff member, I want only moves allowed by the hiring rules to appear as buttons, so that I can't attempt an illegal move.
62. As a staff member, I want a move to update the detail panel, the grouped list and the summary counts together without a page reload, so that the whole page stays accurate.
63. As a staff member, I want a short confirmation toast after a successful move, so that I know it worked.
64. As a staff member, I want an error toast and a refreshed panel when my move is no longer allowed (for example, a colleague already rejected the applicant), so that I see the true current state.
65. As a staff member, I want pipelines of closed jobs to still allow stage moves, so that remaining applicants can be finished off after closing.

### Hiring stage rules

66. As a staff member, I want to move an applicant forward to any later stage, so that a strong candidate can skip stages such as Screening.
67. As a staff member, I want Hired to be reachable only from Offer, so that nobody is hired without an offer being made.
68. As a staff member, I want to move an applicant back exactly one stage, so that I can fix a mis-click without rewriting history.
69. As a staff member, I want to mark an applicant Rejected or Withdrawn from any active stage, so that either side can end the process at any point.
70. As a staff member, I want Hired to be final, so that a completed hire can't be undone by accident.
71. As a staff member, I want to reopen a rejected or withdrawn applicant back to the stage they were in before, so that a change of mind is easy and accurate.
72. As a staff member, I want reopening to be refused while the candidate is archived, with the detail panel telling me to unarchive the candidate first, so that an archived person is never silently put back into an active pipeline.
73. As a staff member, I want moving an applicant to the stage they're already in to do nothing and add no history, so that double clicks don't create noise.
74. As a staff member, I want every stage change to be recorded with who made it and when, so that the hiring process is auditable.

### Dashboard

75. As a staff member, I want the dashboard to show the 25 most recent stage changes across all jobs, so that I can catch up on what happened while I was away.
76. As a staff member, I want each dashboard entry to show the candidate, job, from stage, to stage, who moved them and when, so that each entry is understandable on its own.
77. As a staff member, I want each dashboard entry to link to that applicant on the job's pipeline, so that I can act on it immediately.

### Feedback

78. As a staff member, I want success and error messages for my actions (saving, closing, archiving, moving) shown as toasts that fade away, so that I get confirmation without clutter.
79. As a staff member, I want form validation errors shown next to the field that caused them, so that I know exactly what to fix.

### Development and quality

80. As a developer, I want a demo-data command that creates realistic skills, jobs (including a closed one), candidates (including an archived one) and applications across every stage, with history built through the real stage-move operation, so that I can try every page with lifelike data.
81. As a developer, I want the demo-data command to support a reset option, so that I can return to a known state at any time.
82. As a developer, I want automated tests for every hiring rule and model constraint, so that changes can't silently break the business rules.

## Implementation Decisions

### Stack and tooling

- Python, Django and SQLite, with uv for dependency management.
- Tailwind CSS with DaisyUI through django-tailwind-cli. HTMX for partial page updates.
- Ruff for formatting and linting. pytest with pytest-django, configured in the project's pyproject file.

### Project structure

- The Django project configuration package is named `config`.
- One Django app, `hiring`, holds all domain code: a single models module, a single forms module, and a pure stage-rules module with no database code.
- Views and tests are split into modules by area: candidates, jobs, skills, pipeline and dashboard (plus stage rules for tests).
- Shared templates (base layout, sidebar, toast area) live at the project level. App templates live inside the app, with HTMX fragments kept in a dedicated partials folder.

### Authentication

- Django's built-in authentication and User model, one staff user type, no roles or groups, and no object-level permissions.
- Every view requires login. After login staff are redirected to the dashboard.
- Logout is a POST form in the sidebar.
- Staff accounts are created, deactivated and given password resets only in Django admin. There is no in-app user management or email password reset.
- The app's own models are not registered in Django admin, so admin can't be used to get around the domain rules.

### Models

- **Candidate:** first name, last name, email (required, unique case-insensitively, enforced by a database constraint), optional phone, source (choices: Website, Job Board, Referral, Other), optional source details text, optional resume URL, archived flag.
  - `archive()` raises a validation error if the candidate has any active application (a stage other than Hired, Rejected or Withdrawn). Archiving an already-archived candidate does nothing.
  - `unarchive()` clears the flag.
  - There is no delete in the app.
- **JobOpening:** title, department (plain text), location (plain text), employment type (choices: Full-time, Part-time, Contract, Internship), description, skills (many-to-many to Skill), status (choices: Open, Closed, default Open), closed-at timestamp (nullable), created and updated timestamps.
  - `close()` sets status to Closed and records the closed-at time.
  - `reopen()` sets status to Open and clears the closed-at time.
  - Both do nothing if the job is already in the target state.
  - There is no delete in the app.
- **Skill:** name, unique case-insensitively (database constraint). No delete; mistakes are fixed by renaming.
- **Application:** foreign keys to Candidate and JobOpening, both protected from deletion. Unique constraint on the (candidate, job) pair. Stage (default Applied), optional notes, created and updated timestamps.
  - Model validation refuses new applications for closed jobs and archived candidates.
  - Creating an application writes no history row.
- **StageChange:** foreign key to Application, from stage, to stage, `changed_by` (foreign key to User, protected from deletion), timestamp. No note field.

### Stage rules and the move operation

- The stage choices and transition rules live in the pure stage-rules module. It exposes the set of allowed target stages for a given current stage (plus the history needed for Reopen), and can be unit-tested without a database.
- The rules:
  - From an active stage (Applied, Screening, Interview, Final Review, Offer), an applicant may move forward to any later progress stage, except that Hired is reachable only from Offer.
  - An applicant may move back exactly one progress stage.
  - An applicant may move to Rejected or Withdrawn.
  - Hired allows no moves.
  - Rejected and Withdrawn allow only Reopen, which returns the application to the stage it held immediately before entering Rejected or Withdrawn, determined from its StageChange history.
  - Reopen is refused while the application's candidate is archived. Staff must unarchive the candidate first. This check depends on candidate data, so it is enforced in `move_to()` and the stage move form rather than in the pure stage-rules module. The detail panel replaces the Reopen button with a note saying to unarchive the candidate first.
- All stage changes go through a single `move_to(new_stage, user)` method on Application.
  - It checks the rules, updates the stage, and writes one StageChange row in the same transaction.
  - Moving to the current stage does nothing and writes no history.
  - Disallowed moves raise an error.
- `move_to()` does not check the job's open/closed status; moves stay allowed on closed jobs.

### Forms

- ModelForms:
  - **Candidate form:** all candidate fields except the archived flag.
  - **Job opening form:** all descriptive fields and skills, with no status or closed-at field.
  - **Skill form.**
  - **Application form:** candidate and notes, with the job supplied by the view. The candidate queryset is limited to active candidates without an existing application for that job.
- Plain forms:
  - **Stage move form:** validates that the requested target stage is currently allowed for the application before the view calls `move_to()`.
  - **Candidate list filter form:** search text, source, status of Active / Archived / All (default Active).
  - **Job list filter form:** search text, status of Open / Closed / All (default Open).

### Pages, URLs and behaviour

- **Dashboard:** the 25 most recent StageChange rows across all jobs, loaded with related objects in one query (no per-row queries) and no pagination. Each row links to the job page with that application selected.
- **Candidates:**
  - **List page:** GET filters (search on first name, last name and email, case-insensitive; source; status), filters kept in the query string, no pagination.
  - **Detail page:** information, Edit, Archive / Unarchive POST actions (Archive confirmed with an HTMX confirm prompt), and a read-only table of all the candidate's applications linking to each job page with that application selected.
  - **Create and edit pages.**
- **Job openings:**
  - **List page:** GET filters (search on title and department; status), filters kept in the query string, no pagination.
  - **Create and edit pages.**
  - **Close and reopen:** POST actions that call the model methods. Close is confirmed with an HTMX confirm prompt.
- **Job page (also the pipeline), one URL per job:**
  - **Header:** title, status (with "Closed on [date]" when closed), department, location, employment type, skill badges, and Edit, Close or Reopen, and "Add application" actions. "Add application" is hidden when the job is closed.
  - A collapsible job description.
  - **Summary bar:** one count card per stage, all eight stages including Rejected and Withdrawn. The cards only show counts and don't filter.
  - **Left panel:** applicants grouped by stage, each showing name and days in current stage. Days in stage come from the latest StageChange, or the application's creation time if it has none.
  - **Detail panel:** candidate information (with an "Archived" badge when relevant), current stage, progress stepper, read-only notes, move buttons grouped into Move forward, Fix a mistake and Close out (or a Reopen button for Rejected or Withdrawn, none for Hired), and the stage history timeline.
  - The selected application is a query parameter on the job page URL. Selecting an applicant loads the detail panel with HTMX and pushes the updated URL. A full page load with the parameter renders that applicant selected.
  - **A stage move** is one HTMX POST. The response contains the new detail panel, plus out-of-band swaps for the left list, the summary bar and the toast area.
  - **An invalid move** (for example a stale page) returns status 200 with the fresh detail panel, list and summary plus an error toast.
  - **A same-stage move** re-renders with no toast.
  - **Add application:** a form on the job page that creates the application in Applied.
- **Skills:** a list page with a per-skill job count (one aggregated query), plus create and edit pages.
- **Sidebar:** Dashboard, Candidates, Job openings and Skills, then a list of open jobs linking to their job pages, then the logged-in user and the logout button. There is no separate Pipeline link, because each job's page is its pipeline.

### Feedback

- Django's messages framework for all action feedback, shown as DaisyUI toasts that fade out.
- Full-page responses render messages from the base layout. HTMX responses include the toast area as an out-of-band swap.
- Form validation errors render inline beside their fields.

### Demo data

- A management command creates demo data: several skills, three or four jobs (one closed), about twenty candidates across all sources (one archived), and applications spread across every stage, including rejected and withdrawn ones with history.
- All stage history is created through `move_to()`.
- A reset option clears the app's tables first.
- The acting user is the first superuser, or a newly created demo user if none exists.

### Testing

- Shared pytest fixtures and helper functions provide a candidate, open and closed jobs, a logged-in staff client, and factories for candidates and applications.
- The application helper reaches later stages through `move_to()`, so history exists.
- Test focus:
  - Every from → to stage pair, parametrized.
  - `move_to()` behaviour and history writing, including refusing Reopen for an archived candidate.
  - Model constraints: unique email, unique skill name, unique application, closed-job and archived-candidate blocks, the archive block, close and reopen.
  - Form validation.
  - Login required on every view.
  - List filters.
  - HTMX pipeline responses, including out-of-band content and the invalid-move case.
- No browser or end-to-end tests. Tests target business rules, not a coverage percentage.

## Out of Scope

- Candidate-facing features of any kind: candidate login, a public careers page, self-service applications.
- Roles, groups, per-user permissions, or restricting staff to particular jobs.
- In-app user management, self sign-up and email-based password reset.
- Deleting candidates, job openings or skills inside the app.
- Resume file uploads (only a resume link is stored).
- Skills on candidates, required/preferred skill levels, or skill matching.
- Structured referral tracking (referrer as a linked employee).
- Salary ranges, headcount, target dates or an assigned hiring manager on job openings.
- Automatically rejecting or changing applications when a job closes, or warning about active applications on close.
- A reason or note on individual stage moves, and editing application notes after creation.
- Kanban board or table toggles on the pipeline, drag-and-drop, and bulk moves.
- Filtering the pipeline by clicking summary cards.
- Creating a new candidate and an application in one step, and adding applications from the candidate page.
- Live (as-you-type) search and pagination on list pages.
- Dashboard summaries per job, metrics or charts.
- Email notifications, interview scheduling, calendar integration, and reporting/analytics exports.
- Browser-based end-to-end tests.

## Further Notes

- Two throwaway prototypes informed these decisions and are kept for reference only. They are not production code.
  - **Stage rules comparison:** compared a guided rule set against a simpler one. The guided set was chosen, with the added restriction that Hired is only reachable from Offer, after the prototype showed a skip from Interview straight to Hired.
  - **Pipeline UI:** compared a kanban board, a table with summary bar, and a list and detail review queue. The review queue was chosen with the table's summary bar added, because the kanban was cluttered with move buttons and needed horizontal scrolling.
- The prototype's sidebar still shows a Pipeline link. This PRD replaces it: the sidebar has no Pipeline link.
- The single-entry-point pattern recurs on purpose: `move_to()` for stages, `close()`/`reopen()` for jobs, `archive()`/`unarchive()` for candidates. Each state change has exactly one place where its rules and side effects live, which keeps views thin and rules easy to test.
- Deletion is prevented both in the UI (no delete actions) and in the database (protected foreign keys), so hiring history can't be lost through the app.
