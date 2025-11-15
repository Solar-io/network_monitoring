# Branching, Snapshots, and Releases

Branching Model (Trunk-based)
- main: always releasable; protected; CI checks required.
- feature/<scope>: small scope (1–3 days); draft PR early; squash on merge.
- hotfix/<issue>: from tag or main; quick fix; tag patch release.
- release/<x.y.z>: stabilization branch (optional) for coordinated releases.

Commits & Messages
- Conventional commits: feat|fix|docs|chore|refactor|test(scope): summary.
- Reference issues/decisions: e.g., "Refs ADR-20250910-001".

Session Snapshots (Rollback)
- Create frequent annotated tags to avoid losing work.
- Save:
  - git add -A
  - git commit -m "session: YYYY-MM-DD HH:MM — summary"
  - git tag -a snapshot/YYYY-MM-DD-HHMM -m "Session snapshot"
- Rollback:
  - git checkout -b restore/YYYY-MM-DD-HHMM snapshot/YYYY-MM-DD-HHMM

Releases
- Versioning: semver (x.y.z). Tag releases with vX.Y.Z.
- Checklist:
  - docs/PROJECT_STATUS.md updated with release notes (date/time, features, fixes, migrations, rollback notes).
  - docs/TASKS.md Today cleared/moved; Next reprioritized.
  - Tests/QA/Eval green; known issues documented.
  - Create tag: git tag -a vX.Y.Z -m "vX.Y.Z — summary"; push tags.

Hotfix
- Branch hotfix/<issue> from tag vX.Y.Z; fix; tag vX.Y.(Z+1); update STATUS.

Automation
- scripts/snapshot.sh → creates session tags safely; no-op if clean.
- scripts/release.sh (optional) → validates docs and tags a version.

Cron Examples
- Hourly auto-snapshot (9am–6pm, Mon–Fri):
  - `0 9-18 * * 1-5 /bin/bash -lc "cd /path/to/repo && ./scripts/auto-snapshot.sh"`
- End-of-day snapshot (Mon–Fri):
  - `0 18 * * 1-5 /bin/bash -lc "cd /path/to/repo && ./scripts/snapshot.sh 'end of day'"`
