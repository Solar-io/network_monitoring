# Tool Policies

Allow/Deny
- Allowed by default: read-only fs in workspace, http GET to public sites, git status/diff.
- Deny by default: destructive shell (rm -rf outside workspace), posting credentials, network to private IP ranges.

Working Directory
- All file/shell tools are constrained to `isolation.workspaces_dir/<runId>/<agent>`.
- Writes outside this directory are blocked unless explicitly approved.

Timeouts & Limits
- Default timeouts: shell 20s, http 15s.
- Max output sizes: tool outputs truncated at 200KB (with note) unless explicitly requested.

Redaction
- Apply `replay.redact_patterns` to tool outputs before logging/fixtures.

Schemas
- Tool arguments validated against JSON-like schemas; malformed calls rejected.

Escalations
- Require an approval request for: package installs, system config changes, network POST/PUT, writing executable files.

