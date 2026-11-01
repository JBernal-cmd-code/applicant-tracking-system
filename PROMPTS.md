# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-01 — Phase 8: Stage moves (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 8. Show me the TDD candidates to approve first, then go through RED and GREEN without stopping unless something unexpected happens. Match the move card to option C in prototypes/pipeline-ui.html.`
2. Approved. Make sure the parametrized test also covers Rejected and Withdrawn having no allowed moves for now, since Reopen comes in Phase 9.
3. Verified in the browser, go ahead with PROMPTS.md, commit and push

### Summary
- **Outcome:** Phase 8 is built and committed.
  - **Stage rules:** `hiring/stages.py` gained `allowed_moves()`, which lists each move with its kind (next, skip, back, reject, withdraw), and `allowed_targets()`. The module still has no database code.
  - **Model:** a new `StageChange` model (migration `0005_stagechange`) with protected foreign keys to the application and to `changed_by`, ordered newest first.
  - **`Application.move_to()`:** checks the rules, then saves the new stage and writes one StageChange together in a single transaction. A same-stage move does nothing, and a disallowed move raises `ValidationError`. It doesn't check job status.
  - **Days in stage:** now count from the latest StageChange, else creation. Lists use the `with_stage_entered_at()` annotation, so there's no query per row.
  - **Move form:** `StageMoveForm`, a plain form that checks the target against the stage as currently saved.
  - **Move endpoint:** `POST /applications/<pk>/move/` returns the panel, plus out-of-band swaps for the list, summary bar and toasts. A successful move shows a success toast, an invalid or stale move returns 200 with an error toast, and a same-stage move shows no toast.
  - **Panel:** matches option C. A "Move this application" card shows Move forward, Fix a mistake and Close out groups, or "No moves available." for Hired. The stage history timeline lists each change with who made it and when.
  - **Test helper:** `make_application(stage=...)` now reaches later stages through `move_to()`.
  - **Tests:** 3 TDD tests (the stage-pair test runs 64 cases) and 11 normal tests. That makes 192 passing in total. Ruff, `manage.py check` and the migrations check are clean. The user confirmed the manual browser checks.
- **Deviations:**
  - The user approved all three proposed TDD behaviors: every stage pair, `move_to()` history, and the stale-move HTMX response.
  - The user asked that the parametrized test also assert that Rejected and Withdrawn have no allowed moves until Reopen arrives in Phase 9. It does.
- **Sideways:**
  - The first stage-rules run gave a pytest deprecation warning for passing `itertools.product` to `parametrize`. Wrapping it in `list()` fixed it; this was a mechanical repair with no change to what the test asserts.
  - An existing candidate-page test failed once history existed. It faked a day in stage by backdating `created_at`, but its Final Review application now has a StageChange. Its setup now backdates the StageChange instead, and the assertion is unchanged.
  - Rejected and Withdrawn panels still show the plain alert and an empty stepper. Saying "while in X" depends on the same history lookup as Reopen, so it's left for Phase 9.

## 2026-11-01 — Phase 7: Applicant detail panel, read-only (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 7. Show me the TDD candidates to approve first, then go through RED and GREEN without stopping unless something unexpected happens. Match the detail panel to option C in prototypes/pipeline-ui.html.`
2. approvef
3. Verified in the browser, go ahead with PROMPTS.md, commit and push

### Summary
- **Outcome:** Phase 7 is built and committed.
  - **Panel endpoint:** `/applications/<pk>/panel/` (`hiring/views/pipeline.py`) returns the applicant detail panel. It also sends the applicant list as an out-of-band swap, so the highlighted row follows the selection. A missing application gives a 404.
  - **Shared helper:** `pipeline_context(job, selected_pk)` groups the applicants by stage and picks the selected one from this job's own applications only. The job page now uses it too, reading `?application=<pk>`.
  - **Panel** (`partials/applicant_panel.html`), matching option C:
    - A header card with an initials avatar, the name (linked to the candidate, with an Archived badge), email · source · applied date, and a large stage badge.
    - Contact details: email, phone, source with source details, and the resume link.
    - A progress stepper over the six progress stages, an alert for Rejected, Withdrawn or Hired, and read-only notes.
    - A stage history card.
    - When nothing is selected, the panel says "Select an applicant to see their details."
  - **List rows:** each row loads the panel with `hx-get` and pushes `?application=<pk>` with `hx-push-url`. The `href` is the same URL, as a fallback.
  - **Candidate page:** each application row links to that applicant on the job page.
  - **Stages:** `hiring/stages.py` gained `PROGRESS_STAGES`. `Application.progress_steps` drives the stepper.
  - **Tests:** 11 new tests in `test_pipeline.py`, 3 of them TDD (one parametrized four ways). That makes 115 passing in total.
    - Ruff, `manage.py check` and the migrations check are clean. There is no new migration.
    - The user confirmed the manual browser checks.
- **Deviations:**
  - The user approved all three proposed TDD behaviors as listed: the panel fragment, selected-on-load, and safe handling of a bad `application` parameter.
  - **Departures from option C:** I pointed these out up front, and they were accepted.
    - The "Move this application" card is left out until Phase 8.
    - The stage history only shows the "Applied via [source]" starting entry, because StageChange arrives in Phase 8.
    - Rejected and Withdrawn don't say "while in X" and fill no stepper steps yet.
    - The applied date is shown as a date rather than "N days ago".
- **Sideways:**
  - **TDD 2's first run wasn't RED:** it hit a KeyError (`selected` missing from the context), not an assertion failure. I added the key as scaffolding and re-ran, and it then went RED properly.
  - **TDD 2 test repair:** its "exactly one highlighted row" count also matched the sidebar's `menu-active` on the current job. I limited the count to the pipeline list, which was a mechanical fix with the same assertion.
  - **TDD 3 never went RED:** it passed on its first run, because test 2's code already compares ids as text within the job's own applications. To prove the test wasn't vacuous, I swapped in a naive `Application.objects.get()` for a moment. It failed 3 of the 4 cases (it selected a foreign applicant and crashed on `abc` and `999999`), then I reverted it. I reported this rather than stopping mid-phase.
  - **TDD 1 weakness:** the "Interview" check would also match the stepper label, so it doesn't prove the stage badge on its own.

## 2026-11-01 — Phase 6: Applications — add from the job page, pipeline list and summary bar (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 6. Show me the TDD candidates to approve first, then go through RED and GREEN without stopping unless something unexpected happens. Match the summary bar and grouped applicant list to option C in prototypes/pipeline-ui.html.`
2. Apprved
3. Verified in the browser, go ahead with PROMPTS.md, commit and push

### Summary
- **Outcome:** Phase 6 is built and committed.
  - **Stages:** a new pure module, `hiring/stages.py`, holds the eight `Stage` choices. The transition rules come in Phase 8.
  - **Model:** `Application` has PROTECT foreign keys to candidate and job, a unique (candidate, job) constraint, a stage defaulting to Applied, notes, and created/updated times. It's added in migration `0004_application`.
    - `clean()` refuses a *new* application to a closed job. Existing applications on a closed job still validate.
    - `days_in_stage` counts from the creation time until stage history arrives in Phase 8.
  - **Form:** `ApplicationForm` is a ModelForm with candidate and notes. It takes the job from the view.
    - The candidate queryset offers only active candidates who haven't applied to this job.
    - A custom `invalid_choice` message explains why a stale submission is refused.
  - **Pages:**
    - **Add application:** `/jobs/<pk>/applications/new/` is a form page. On a closed job it redirects back with an error toast. The "+ Add application" button shows only on open jobs.
    - **Job page:** a summary bar with eight count cards, and a grouped applicant list with stage headers, counts, initials avatars and days in stage. Both are partials (`pipeline_summary.html`, `pipeline_list.html`) with ids and an `oob` flag, ready for Phase 8.
    - **Candidate page:** an Applications table showing job (linked), stage badge and days in stage.
    - **Shared partials:** `stage_badge.html` and `days_in_stage.html`.
  - **Fixtures:** `conftest.py` gained `make_application`.
  - **Tests:** 18 new tests in `test_pipeline.py`, 3 of them TDD, for 104 in total.
    - Ruff, `manage.py check` and the migrations check are clean.
    - The user confirmed the manual browser checks.
- **Deviations:**
  - The user approved all three proposed TDD behaviors as listed: closed-job model validation, the form's candidate queryset, and the stale duplicate form error.
  - **Prototype mismatch:** option C in the prototype has no summary bar. That bar comes from option B, as the PRD records. I used B's count cards without the click-to-filter behavior, plus C's grouped menu list. I pointed this out when I listed the TDD candidates, and the user didn't object.
- **Sideways:**
  - **All three REDs were honest assertion failures:**
    - Behavior 3: "DID NOT RAISE ValidationError".
    - Behavior 1: the archived candidate and the already-applied candidate were extra items in the queryset.
    - Behavior 2: the stale submission was already refused, but with Django's generic "Select a valid choice" message, so the test failed on the message.
  - **Simultaneous-submit race:** two submissions at exactly the same moment would both pass the form, and the second would hit the database constraint as a 500 error, not a form error. I flagged this but didn't handle it.
  - **Temporary list links:** clicking an applicant in the pipeline list opens their candidate page until the Phase 7 detail panel replaces it. The right-hand pipeline column is empty for now.
  - **Test cleanup:** I first wrote a test helper that created a second job by hand. I replaced it with the existing `make_job` fixture before running the tests.

## 2026-11-01 — Phase 5: Close and reopen jobs, and job list filters (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 5. Show me the TDD candidates to approve first, then go through RED and GREEN without stopping unless something unexpected happens.`
2. approved, go ahead
3. Make closing jobs easier to find. Add a Close or Reopen button next to Edit on each row of the job openings list, using the same POST views, confirm prompt, and job.close()/reopen() methods. Also add a short note on the job edit form saying to use the Close button on the job page to close the job. Add tests for the new list buttons.
4. verified, it all works — go ahead and finish the phase

### Summary
- **Outcome:** Phase 5 is built and committed.
  - **Model:** `JobOpening.close()` sets Closed and stamps `closed_at`, and `reopen()` sets Open and clears it. Each returns early if the job is already in the target state, so a second close keeps the original date. No migration was needed.
  - **Form:** `JobFilterForm` is a plain form with search (title or department, case-insensitive) and status (Open / Closed / All, default Open). It follows the `CandidateFilterForm` pattern.
  - **Views:** `job_close` and `job_reopen` are POST-only and call the model methods, then show a toast. An HTMX request gets an `HX-Redirect` to the job page, so the confirm prompt's request reloads the full page. A plain POST gets a normal redirect.
  - **Pages:**
    - The job page header shows "Closed on [date]" and either Close (an `hx-post` with `hx-confirm`) or Reopen (a plain POST form).
    - The job list has the GET filter form, kept in the URL.
    - Closed jobs drop out of the sidebar through the existing context processor.
  - **Follow-up request:** every job list row now has Close or Reopen next to Edit. The button lives in a shared partial, `partials/job_close_reopen_button.html`, used by both the header and the list. The edit form has a note pointing to the Close button on the job page.
  - **Fixtures:** `closed_job` in `conftest.py` now closes its job through `close()` instead of setting the status directly.
  - **Tests:** 20 new tests, 2 of them TDD, for 86 in total.
    - Ruff, `manage.py check` and the migrations check are clean.
    - The user confirmed the manual browser checks.
- **Deviations:**
  - I proposed two TDD behaviors, `close()` and `reopen()` with their no-op rules. I left out the list filters because they copy the already-tested candidate filter pattern. The user approved both.
  - After the first browser check, the user asked for Close/Reopen buttons on the job list rows and a note on the edit form, beyond the plan.
- **Sideways:**
  - **Not a real RED:** the first run of the `close()` test failed with an `AttributeError` because the method didn't exist yet, which isn't an assertion failure. I added empty `close()`/`reopen()` stubs, and the test then failed on `'open' == 'closed'`.
  - **Replaced test:** the Phase 4 test "list shows open and closed jobs" no longer held once the list defaulted to Open. I replaced it with the parametrized status filter test.
  - **Redirect from the list:** closing or reopening from a list row reuses the same views, so it lands on the job page rather than back on the list. I pointed this out and offered to return to the referring page. The user accepted the current behavior.
  - **Weak assertion:** the edit-form note test also checks for a link to the job page, but the form's Cancel link already points there. The test's text assertion is what actually covers the note.

## 2026-11-01 — Phase 4: Job openings — create, edit, list and job page header (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 4. Show me the TDD candidates to approve first, then go through RED and GREEN without stopping unless something unexpected happens.`
2. Approved
3. Everything passed in the browser, go ahead with PROMPTS.md, commit and push

### Summary
- **Outcome:** Phase 4 is built and committed.
  - **Model:** `JobOpening` has employment type choices (Full-time, Part-time, Contract, Internship), a status (Open / Closed, default Open), a nullable closed-at time, created and updated times, and a many-to-many link to `Skill` with `related_name="job_openings"`. It's added in migration `0003_jobopening`.
  - **Form:** `JobOpeningForm` is a ModelForm with the descriptive fields and skills, shown as checkboxes. It has no status or closed-at field.
  - **Pages:** a basic job list, create and edit pages, and the job page at `/jobs/<pk>/`. The job page header shows the title, an Open/Closed badge, department, location, type, skill badges and an Edit button, with the description in a DaisyUI collapse. All are function views in `hiring/views/jobs.py`. There is no delete action.
  - **Sidebar:** the Job openings link is live. A new context processor, `hiring/context_processors.py`, gives every page the open jobs, and the sidebar lists them under "Open jobs".
  - **Skills list:** counts now come from `Count("job_openings")`.
  - **Fixtures:** `conftest.py` gained `make_job`, `open_job` and `closed_job`. The closed job sets its status directly until Phase 5 adds `close()`.
  - **Tests:** 21 new tests, 3 of them TDD, for 66 in total.
    - Ruff, `manage.py check` and the migrations check are clean.
    - The user confirmed the manual browser checks.
- **Deviations:** none. The user approved the three proposed TDD behaviors as listed: new jobs start Open, the sidebar lists open jobs on every page, and the Skills list shows real job counts.
- **Sideways:**
  - **Getting an honest RED for the default status:** I had already written `default=Status.OPEN` into the model, so the behavior 1 test would have passed as soon as it was written. I took the default back out and regenerated the migration, which made the test fail on `'' == 'open'`. Then I put the default back as the GREEN step and regenerated the migration again.
  - **Skills ordering regression:** switching the job count to `Count("job_openings")` broke the alphabetical order of the Skills list, because Django ignores `Meta.ordering` on aggregated queries. The existing ordering test caught it, and an explicit `.order_by("name")` fixed it. The tests themselves didn't change.
  - **Checkbox styling:** after the tests passed, I added DaisyUI `checkbox` classes to the skills widget, because Django renders the checkbox tags itself.

## 2026-11-01 — Phase 3: Candidates — create, edit, detail, search and filters (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 3, and keep going through the TDD behaviors without asking unless something unexpected happens`
2. (Interrupted the agent while it was running the behavior 2 test.) I didn’t get to approve the TDD candidates for this phase. List the behaviors you tested and show me each test, so I can review them now.
3. Approved, both tests are good. Also add TDD behaviors for the database rejects a case-insensitive duplicate email, the candidate form shows the duplicate email error on the email field, and the source filter. If any of them pass immediately because the code was already built, say so and keep them as regression tests. Then run them through red and green without stopping unless something unexpected happens.
4. Two UI fixes. On the candidates list, add a visible Edit button at the end of each row, like the Skills list. On the candidate detail page, make Edit a real DaisyUI button placed next to the candidate’s name instead of plain text in the far corner. Clicking a name in the list should still open the detail page.
5. Everything passed in the browser. Go ahead with PROMPTS.md, commit and push. In the Sideways section, note that the TDD candidate approval step was skipped at the start of this phase because of my prompt wording, and that I caught it, stopped the agent, reviewed the tests, and added the missing email and source filter tests. Also note the Edit button fix.

### Summary
- **Outcome:** Phase 3 is built and committed.
  - **Model:** `Candidate` has a `Source` choice list (Website, Job Board, Referral, Other), an archived flag, and a case-insensitive unique constraint on `Lower("email")`, added in migration `0002_candidate`.
  - **Forms:**
    - `CandidateForm` is a ModelForm that leaves out the archived flag. Its `clean_email()` puts a duplicate email error on the email field, the same way the Skill form does.
    - `CandidateFilterForm` is a plain form with search, source and status (Active / Archived / All, default Active). Its `filter()` method applies them to a queryset.
  - **Pages:** a list page with GET filters kept in the URL, a detail page, and create and edit pages, all function views in `hiring/views/candidates.py`. The sidebar Candidates link is live. There is no delete action.
  - **Fixtures:** `conftest.py` gained `make_candidate` and `candidate`.
  - **Tests:** 24 new tests, 5 of them TDD, for 45 in total.
    - Ruff, `manage.py check` and the migrations check are clean.
    - The user confirmed the manual browser checks.
- **Deviations:**
  - I proposed only two TDD behaviors: search, and the status filter defaulting to Active. I left out email uniqueness because the tested Skill pattern already settled it. The user approved both, then added three more: the database email constraint, the inline email form error, and the source filter.
  - **Already-built TDD behaviors:** the email constraint and the email form error tests passed as soon as they were written, because that code had been built along with the model and form. The user had asked in advance to keep tests like these as regression tests, so they were kept. The source filter test went RED, then GREEN.
- **Sideways:**
  - **Skipped candidate approval:** I didn't stop for approval of the TDD candidate list. I read the prompt’s “keep going through the TDD behaviors without asking” as covering that step too.
    - By then I had finished behavior 1 (search) through red and green, and written behavior 2’s test.
    - The user caught it while I was running the behavior 2 test, stopped me, and had me list the behaviors and show each test.
    - After reviewing the tests, the user approved them and added the missing email constraint, email form error and source filter tests.
    - I saved a memory: always stop after the candidate list, even under "keep going".
  - **Edit buttons:** after the first browser check, the user found the Edit actions weak.
    - The list had no Edit action per row. It now ends each row with an Edit button styled like the one on the Skills list.
    - The detail page's Edit sat in the far corner and looked like plain text. It is now an outlined primary button next to the candidate's name.
    - A test now checks that each list row has both its detail link and its edit link.
  - **Filter fallback:** if the filter form is invalid (for example `?status=bogus`), `filter()` ignores every filter and shows active candidates. That was a choice I made myself and wasn't raised with the user.

## 2026-11-01 — Phase 2: Skills (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 2`
2. yes, approved
3. yes, approved
4. yes, move on to behavior 2
5. Yes, that’s correct. Go ahead, and keep going through the rest of the phase unless something unexpected happens.
6. All checks passed, go ahead and finish the phase

### Summary
- **Outcome:** Phase 2 is built and committed.
  - **Model:** `Skill` has a case-insensitive unique constraint on `Lower("name")`, in a single `0001_initial` migration.
  - **Form:** `SkillForm` is a ModelForm. Its `clean_name()` checks for case-insensitive duplicates, excluding the skill being edited.
  - **Pages:** a Skills list, plus create and edit pages, all function views in `hiring/views/skills.py`. Successful saves show toasts. The sidebar Skills link is live. There is no delete action.
  - **Tests:** 14 new tests, 2 of them TDD, for 21 in total. Ruff, `manage.py check` and the migrations check are clean. The user confirmed the manual browser checks.
- **Deviations:**
  - I proposed only two TDD behaviors, not three. I left the job count out because `JobOpening` doesn't exist until Phase 4. The user approved both.
  - The user approved behavior 2's test and told me to finish the rest of the phase without stopping, so the green summary for behavior 2 and the normal tests weren't paused for review.
- **Sideways:**
  - **Constraint error placement:** behavior 2 went RED because Django reports an expression-based constraint (`Lower("name")`) as a form-wide `__all__` error instead of a field error. `clean_name()` fixed it. The database constraint stays as the final guard.
  - **Migration replaced:** the first `0001_initial` migration was generated without the constraint so behavior 1 could fail. Since nothing had been committed or applied, I deleted it and regenerated it with the constraint.
  - **Placeholder job count:** the list annotates `job_count` with a constant `Value(0)`, marked by a comment to become `Count("job_openings")` in Phase 4. The single-query criterion is covered by a test that the query count doesn't grow with the number of skills.
  - **Test rewrite:** my first query-count test was muddled (it re-ran the queryset with an unused variable). Before running it, I replaced it with the comparison of query counts at one and five skills.

## 2026-11-01 — Phase 1: project skeleton, authentication and app shell (implement + TDD)

### Prompts
1. `/implement @prd/applicant-tracking-system.md @plans/applicant-tracking-system.md implement Phase 1`
2. Approved, go ahead with all three
3. Approved, use the middleware
4. Yes, go ahead with behavior 2
5. Approved, go ahead
6. Yes, go ahead with behavior 3
7. Keep it as a regression test, go ahead
8. Manual verification passed, go ahead and finish the phase

### Summary
- **Outcome:** Phase 1 is built and committed.
  - **Project:** a uv project (Django 6.1, django-htmx, django-tailwind-cli; pytest, pytest-django and Ruff as dev dependencies) with the `config` project and the `hiring` app. Views and tests are packages split by area. `hiring/admin.py` was removed so no app models can be registered in admin.
  - **Auth:** `LoginRequiredMiddleware` makes every view require login. `LOGIN_REDIRECT_URL` points to the dashboard. Django's auth URLs give the POST-only logout. A small `StaffLoginView` adds a "Welcome back" success message.
  - **Shell:** a base layout, a sidebar (four main links, current user, POST logout), a toast area that fades messages out with CSS and removes them with a small script, a DaisyUI login page and a placeholder dashboard. The toast template takes an `oob` flag for later HTMX responses.
  - **Tailwind:** DaisyUI comes from the tailwind-cli-extra binary, pinned to 2.10.34. The source is `assets/css/source.css`. The binary, the generated CSS and `db.sqlite3` are git-ignored. HTMX is served from django-htmx's own copy.
  - **Tests:** 7 pytest tests (3 TDD, 4 normal). Ruff check and format, `manage.py check` and the migrations check are clean. The user confirmed the manual browser checks.
- **Deviations:**
  - The user approved all three proposed TDD behaviors and chose the login middleware I recommended over per-view decorators.
  - Behavior 3 (logout ends the session) could not go RED. The user agreed to keep it as a regression test.
- **Sideways:**
  - **Pre-built behavior:** during scaffolding I had already added `LoginRequiredMiddleware` and `LOGIN_REDIRECT_URL`, which would have made behaviors 1 and 2 pass without a RED step. I removed each setting before writing its test, showed the failing assertion, then put it back.
  - **Logout already green:** behavior 3 passed on its first run because Django's built-in `LogoutView` came with the auth URLs the scaffolding needed. I reported this instead of forcing a staged failure.
  - **Unasked feature:** the "Welcome back" login toast isn't a PRD story. I added it so the toast criterion could be checked in Phase 1.
  - **Environment:** the shell's `VIRTUAL_ENV` points at another project (book-catalog). uv warns about it and ignores it. A Bash `cd` briefly moved the working directory into the site-packages folder, which I corrected. My first HTMX smoke check requested the wrong file name (`htmx.min.js` instead of `htmx-2.min.js`), and the real file served fine.

## 2026-11-01 — Initial CLAUDE.md for the ATS

### Prompts
1. Create the initial CLAUDE.md for this project.

   Keep it to about 20-30 lines. Include only:
   1. A one-line project description.
   2. The approved technology stack and package manager.
   3. Durable, project-wide architecture decisions already established in the PRD.
   4. Short pointers to the PRD, plan, and prototypes instead of repeating their details.

   Do not add commands yet because the project tooling has not been installed or verified.
   Do not predict project structure, paths, template conventions, URL conventions, or testing commands that do not exist yet.
   Do not copy business requirements, user stories, implementation phases, rejected alternatives, or detailed feature rules into CLAUDE.md.
   Do not invent new architectural conventions.
2. rite this session log to PROMPTS.md according to its instructions.

### Summary
- **Outcome:** `CLAUDE.md` at the repo root (about 25 lines), written after reading the PRD and plan.
  - It has a one-line description, the stack with uv as the package manager, the PRD's durable architecture decisions, and pointers to the PRD, plan and `prototypes/`.
  - It has no commands, URLs, template layout or feature rules. I left out the planned `config` and `hiring` package names because those packages don't exist yet.
  - It is uncommitted.
- **Deviations:** none. The user asked no follow-up questions.
- **Sideways:**
  - **Redundant bullet:** my draft had a separate bullet saying `move_to()` is the only way to change a stage and writes history in one transaction. That repeated the single-entry-point bullet and added a detailed feature rule the prompt excluded. The user removed it from the file directly after the session's first prompt.

## 2026-11-01 — Implementation plan for the ATS from the PRD (prd-to-plan)

### Prompts
1. `/prd-to-plan @prd/applicant-tracking-system.md`
2. Let's merge phases 3 and 4, and merge 10 and 11, and also merge 12 and 13. Keep phase 9 as one phase. Archive before reopen is the right order. Fix the phase 4 note to point to the archive phase. Please write the final plan file.
3. Write this session log to PROMPTS.md according to its instructions.

### Summary
- **Outcome:** `plans/applicant-tracking-system.md`, a 10-phase vertical-slice plan covering all 82 PRD user stories.
  - The header records the durable decisions: stack, the `config` and `hiring` layout, template locations, models, stages, single entry points, auth, no deletion, and how feedback is shown.
  - The phases: skeleton/auth, skills, candidates with filters, job openings, close/reopen with job filters, applications with the pipeline list, the detail panel, stage moves, archive with reopen, and dashboard with demo data.
  - No application code was written. The plan is uncommitted.
- **Deviations:**
  - I proposed 13 phases. The user merged three pairs: candidates CRUD with candidate filters, archive with reopen, and dashboard with demo data.
  - I offered to split the stage-moves phase into two. The user kept it as one phase.
  - The user confirmed my archive-before-reopen order.
- **Sideways:**
  - **Wrong phase reference:** my first breakdown said the candidate Archived filter would only have data "once phase 11 exists", but archiving was in phase 10. Instead of correcting it, I added a separate "(Fix: …)" line below the list. The user asked for the note to point to the archive phase, which is Phase 9 in the final plan.
  - **URLs not in the PRD:** the PRD doesn't specify URL paths. I chose them myself and put them in the plan header, including two HTMX-only URLs (`/applications/<pk>/panel/` and `/applications/<pk>/move/`). I pointed this out when I handed over the plan, but the user hasn't reviewed them yet.

## 2026-11-01 — Design interview (grill-me), two prototypes, and the PRD for the ATS

### Prompts
1. `/grill-me @project-idea.md`
2. Option a. It should be one staff user type with Django's built in login. Every page should also require a login. There should also be no roles.
3. Option A, and email should be required, unique, and case-insensitivie. Fields should include first name, last name, email phone as an optional choise, source (only website, job board, referall, other) and an optional resume link. No resume upload should be there.
4. Option B and add an optionla soruce details text field. There should be no validation required.
5. Option B, department and location should be plain text fiields and not seperate tables.
6. Option A with (i), and skill model with a unique, case-insensitive name, and a many to many filed on job opening. Skills should be managed on a separate skills page, and the job form picks from exisiting skills.
7. Option B, track stage history with a stage change model, and all stage changes go through one move_to()method. And no note on stage changes. And yes to the optional general notes filed and created/updated time stamps.
8. `/prototype` can you prototype the hiring stage transition rules from the latest question in our grill? Let me compare options C and D side by side. Include walkthroughs for skipping forward, moving back on setp to fix a mistake, rejecting then reopening, trying to move a hired applicant, and moving to the same stage iti is already in.
9. C, but Hired can only be reached from Offer. The prototype showed C let someone skip from Interview straight to Hired without an offer. Same-stage moves should quietly do nothing and not add history.
10. For 8 a yes to reopening is allowed with a closed_at timestamp. For 8 b, do option (i) nothjing automatic. Closing only blocks new applications. For 8c, go with the recommendation to block new applications on closed jobs in the model, and still allow stage moves on existing applications.
11. Option B, let's do an archve instead of delete, with no delete in thge app. Use on_delete=PROTECT on applications's foreign keys to candidate and job openings. And yes to the sub question, block archiving while a canidate has an active application.
12. `/prototype` can you prototype the hiring pipeline page from the latest question in our grill? Build 3 structurally different versions using Tailwind and DaisyUI from the CDN. First, kanban board for one job opening with the 6 progress stages as columns and rejected/withdrawn in a collapsed closed out section. And a table view for one job opening with stage filters and a summary bar showing counters per stage. Also add a layout of your choice that is different from the first two. I also want the overall layout to be clean and modern. A sidebar for navigation, cards with good spacing, rounded corners, stage badges, and a professional look. Use realistic but fake data with around 15 applicatns athat can be spread across the stages. Each applicant should be allowed-move buttons based on my stage rules. And clicking a button should move the application memory so I can feel how it works.
13. Optioon c, the list and detail layout, but I want the stage count summary bar from option B added at the top. The kanban board felt cluttered with so many move buttons on every card and it needed horizontal scrolling, while option C shows the whole pipeline grouped by stage and organizes the moves by my transition rules. I want to keep the sidebar navigation with Dashboard, Pipeline, Candidates, Job openings, Skills and the list of open jobs. The summary bar should have a count card for every stage including Rejected and Withdrawn. The left panel should show applicants grouped by stage with their days in stage, and the right panel should show the selected applicant's info, the progress stepper, the move buttons grouped into Move forward, Fix a mistake and Close out, a Reopen button for rejected or withdrawn applicants, and the stage history timeline. When I move an applicant it should use HTMX to update just the detail panel, the left list and the summary counts without reloading the page. I don't want a board and table toggle, bulk moves, or a reason field on moves.
14. OPtion A, this will be from the job's pipeline page only, with existing candidates only. The assumptions you made are good. Also, the stage movbe should use a plain forms.form not a ModelForm that validates the target stage before cvalling move_to(). The candidate, job, skill,, and application forms can be ModelForms.
15. Option C, the dashboard is a recent acitivity feed showing the latest stage changfes across all jobs, with links to each applicant's pipelin. Staff land here after login.
16. Option B simple get filters on both listsm buitl with a plain forms.Form, and candidates default to active and jobs default to open. Thee should be no pagination.
17. Option A, staff accounts will be managfed through Django admin only. The defaults look right, post logout in the sidebar, no email password rest, protect on changed_by and dont register the app models in admin.
18. Can we do a mix of A and C? I want one hiring app with a single models.py but split views and tests  into modules by area (such as candidates, jobs, pipeline, and dashboard). The supporting defaulrts look right, confgi/ for the projet, shared templates at the top level, partials in partials/ subfolder, and stage rules in a pure stages.py moduel.
19. Option B, shared fixtures in conftest.py, defaults look right
20. Option B, dedicated close and reopen buttons with model methods, and use hx-confirm on close.
21. Option a, one page where the pipeline is the job detail page with a collapsible description.
22. Option A, candidate detail page with read-only applications. HTe archive mehchanics also look right
23. Option A, messages as toasts, defaults look right
24. Option B where notes a re set on the add application form and shown read only in the detail panel.
25. Option A, no delete, and show the job count per skill
26. Option B, a seed_demo management command using move_to()
27. The sidebar Pipeline link doesn't have a page of its own since each job is its own pipeline. Remove the Pipeline link and keep the open jobs list in the sidebar.
28. `/to-prd`
29. Reopen should be refused if the candidate is archived. Staff must unarchive the candidate first. Add that to the stage rules section and the user stories.
30. Write this session log to PROMPTS.md according to its instructions.

### Summary
- **Outcome:** A 23-question design interview covering every requirement in `project-idea.md`, two throwaway prototypes, and a PRD.
  - `prototypes/stage-rules-c-vs-d.html` puts the two candidate stage rule sets (C and D) side by side, with five guided walkthroughs.
  - `prototypes/pipeline-ui.html` shows three pipeline layouts (kanban, table + summary bar, review queue) in Tailwind/DaisyUI, with in-memory moves.
  - `prd/applicant-tracking-system.md` has 82 user stories, implementation decisions and the out-of-scope list.
  - No application code was written. The prototypes and PRD are uncommitted.
- **Deviations** (places where the user overrode my recommendation):
  - **Stage rules (Q7):** took Option C but added "Hired only from Offer". Same-stage moves are a silent no-op rather than the refusal message the prototype showed.
  - **Job close (Q8b):** nothing automatic and no warning screen, instead of the recommended "allow closing, but warn first" (iv).
  - **Candidate lifecycle (Q9):** archive with no delete at all (B), instead of archive plus delete-only-when-no-applications (C).
  - **Pipeline UI (Q10):** chose the review queue (list and detail) with the table's summary bar added, instead of the recommended kanban with buttons. The user explained the kanban was cluttered and needed horizontal scrolling.
  - **Adding applications (Q11):** from the job's pipeline page only, instead of both the pipeline and the candidate page. The user also added that the stage move must use a plain `forms.Form` that validates the target before `move_to()`, while the other forms are ModelForms.
  - **Dashboard (Q12):** a recent activity feed (C), instead of the recommended per-job overview cards (B).
  - **List pages (Q13):** plain GET filters (B) instead of HTMX live search (C), and no pagination instead of 25 per page.
  - **Project structure (Q15):** a mix of A and C. One `models.py`, but views and tests split by area.
  - **Application notes (Q21):** set only when the application is created and read-only afterwards (B), instead of the recommended HTMX inline edit (A).
  - **After the interview:** the user removed the sidebar Pipeline link, and added "Reopen refused while the candidate is archived" to the PRD.
- **Sideways:**
  - **Pipeline link:** my design summary kept a sidebar "Pipeline" link even though Question 18 had made each job page its own pipeline, so the link had no page to go to. The user caught it. The throwaway UI prototype still shows the link, and the PRD notes that it was replaced.
  - **Archived-candidate reopen:** the rule gap where an archived candidate's Rejected or Withdrawn application could be reopened (the Question 7 and Question 9 decisions didn't account for each other) wasn't caught during the interview. The user found it after the PRD was written, and the PRD was patched: new story 72, a new stage rule, and a test note.
  - **Kanban collapse bug:** the "Closed out" section in the kanban prototype snapped shut after every move because the page re-renders. I caught this before handing the prototype over and fixed it by remembering whether the section was open.
  - **Prototype rendering:** both prototypes were opened in the browser, but I never checked their rendering visually. The UI prototype depends on pinned CDN versions (DaisyUI 5.0.0, Tailwind browser 4.0.0).
