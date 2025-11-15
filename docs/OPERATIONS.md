# Operations Runbook

Environment
- Copy `.env.example` to `.env` and fill in provider keys if using direct APIs.
- Configure project defaults in `config/project.yml`.

Daily
- Start session: `scripts/new-session.sh` and fill `docs/TASKS.md`.
- End session: update STATUS/TASKS, snapshot: `scripts/snapshot.sh "end of session"`.
- Hourly snapshots: configure cron to call `scripts/auto-snapshot.sh`.

Running Orchestrations (HTTP)
- POST `/api/chat` with `{ threadId, messages[], selectedAgents[], tools[], vars{} }`.
- Stream via SSE `/api/stream?runId=...` and render events in the Run Panel.

Replay
- Enable fixtures in `config/project.yml`. Re-run a `runId` in replay mode to stub external calls from `fixtures/runs/<runId>`.

Provider Options
- Direct APIs: OpenAI, Anthropic, Azure OpenAI (env vars in `.env.example`).
- IDE Assistants (VS Code): GitHub Copilot, Claude Code, OpenAI Chat — encouraged for coding but:
  - Always update docs (STATUS/TASKS/BUGLOG/EXPERIMENTS) as you go.
  - Keep diffs minimal and focused; snapshot before large refactors.
  - If assistants modify code, ensure changelog entries and link to snapshot tags.

Budgets & Caps
- Respect caps in `config/project.yml` and env overrides. UI should warn at 80% and pause for confirmation on exceed.

Approvals
- Risky operations require an approval event and explicit confirmation; snapshot before proceeding.

