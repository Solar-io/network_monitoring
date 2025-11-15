# Experiments

Guidelines
- Capture prompt/model/config details to ensure repeatability.
- Record outcomes (metrics + qualitative), decision, and next action.

Table (recent)
| ID | Date | Goal | Model/Provider | Data/Task | Result | Decision |
|----|------|------|----------------|-----------|--------|----------|
| EXP-YYYYMMDD-001 | YYYY-MM-DD | | | | | |

Entry Template
---
ID: EXP-YYYYMMDD-001
Date: YYYY-MM-DD HH:MM TZ
Goal:
- 
Setup:
- Model/version, provider, parameters (temperature, top_p, max_tokens, tools)
- Prompt(s) and system instructions
- Dataset/task slice
Metrics:
- 
Observations (qualitative):
- 
Result:
- (success/fail/neutral)
Decision:
- adopt/iterate/drop; next step
Links:
- PR/commit/tag, session log
---

Notes on Repro & Versioning
- Record `runId` and prompt/tool schema hashes with each experiment to ensure provenance.
- If fixtures are enabled, include path to `fixtures/runs/<runId>` to allow offline replay.
