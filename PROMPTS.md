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
