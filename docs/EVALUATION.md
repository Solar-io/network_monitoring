# Evaluation Plan

Goals
- Track quality, safety, latency, and cost across prompts, tasks, and releases.

Metrics
- Task success (%), exact-match/semantic scores, human ratings (Likert), latency p50/p95, token/cost per task, safety flags.

Datasets & Tasks
- Golden tasks: small curated set covering core workflows.
- Regression set: recent bugs converted to tests.
- Stress set: long inputs, edge tools, rate-limit scenarios.

Process
- Nightly eval run on main; per-PR lightweight checks.
- Diff report: deltas vs last release and last 7 days.
- Store runs in DB; link to run IDs from UI.

Replay Fixtures
- Record fixtures (`config.project.yml → replay`) during evals to enable deterministic replays.
- On regression, replay failing run with fixtures and compare events and outputs.

Acceptance Gates
- No significant regressions on golden set; safety violations must be 0.

Tooling
- Use a simple runner script or LangSmith/OpenAI Evals-like harness; export CSV/JSON.
 - Add a replay mode to stub tool calls from `fixtures/runs/<runId>` for offline verification.
