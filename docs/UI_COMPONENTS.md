# UI Components (Web, AI-First)

Principles
- Accessibility: keyboard nav, ARIA roles, focus traps, prefers-reduced-motion.
- Streaming-first: seamless token streaming (SSE/WebSocket), graceful backpressure.
- Observability: visible run IDs, timing and token counters, trace links.
- Resilience: local draft persistence, retry affordances, offline hints.

Core Components
- Thread List
  - Props: `items`, `selectedId`, `onSelect`, `onCreate`, `onArchive`, `onSearch(query)`
  - States: `loading`, `empty`, `error`, `filtered`
  - Acceptance: keyboard-accessible; 10k threads virtualized; fuzzy search.

- Chat Transcript
  - Props: `messages`, `onRetry(id)`, `onCopy(id)`, `onShare(id)`, `onExpandTool(id)`
  - States: `streaming`, `collapsed tool result`, `error segment`
  - Acceptance: virtualization >5k messages; code blocks copy; citation chips.

- Message Bubble
  - Props: `role`, `content`, `annotations` (sources/tools), `metrics` (latency/tokens/cost)
  - Patterns: hover actions (copy, retry, quote), expandable tool outputs.

- Composer
  - Props: `value`, `onChange`, `onSubmit`, `disabled`, `selectedAgents`, `variables`
  - Features: slash-commands, template insertion, variable prompts, file attach, token budget bar.
  - A11y: announce streaming start/stop; maintain cursor position predictably.

- Agent/Tool Picker
  - Props: `options` (capabilities, cost), `multi`, `onChange`, `recommended`
  - Display: badges for network, filesystem, shell, git, code-edit permissions; toggles for risky scopes (require confirm).

- Run Panel (Trace View)
  - Props: `runId`, `events` (timeline), `onExpand`, `onDownload`
  - Events: plan, delegate, tool-call, tool-result, error, summary; filters by agent.

- Prompt Template Library
  - Props: `templates`, `onApply`, `onSave`, `variables`
  - Features: preview with variables; diff against current; favorites.

- Eval Dashboard
  - Props: `datasets`, `runs`, `filters`, `onCompare`
  - Views: table, small multiples, regression deltas; cost and latency histograms.

- Settings Panel
  - Props: `config`, `onChange`, `onTest`
  - Sections: providers/keys, safety, caching, files, rate limits, telemetry opt-in.

- File Uploader & Vault
  - Props: `files`, `onUpload`, `onRemove`, `onPreview`
  - Show: ingest progress, parse errors, tokenized size estimates.

- System Status Bar
  - Props: `env`, `indicators`, `budgets`, `onDetails`
  - Show: model limits, token/cost usage vs caps, rate-limit status, backend connectivity.

Patterns
- Streaming: render tokens incrementally; keep composer active unless tool requires lock.
- Errors: show concise message with `runId` and “replay with same context”.
- Persistence: store drafts and UI state per thread; restore on reload.
 - Budgets: display token and cost progress bars per run; warn at 80%.

Wireframe Notes
- Layout: left thread list (collapsible), center chat, right trace panel.
- Breakpoints: mobile shows tabs (Chat | Trace | Threads).
