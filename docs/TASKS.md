# Tasks

Last updated: 2025-01-06

## Blocked

_No blocked tasks currently_

## M1 — Foundation & Infrastructure ✅

- [x] Create project directory structure
- [x] Set up Dockerfile and docker-compose.yml
- [x] Create requirements.txt with dependencies
- [x] Configure .env.example and .gitignore
- [x] Initialize git repository

## M2 — Database Layer ✅

- [x] Implement SQLAlchemy models (Host, Heartbeat, Alert, LogAnalysis, Config)
- [x] Create Pydantic schemas for validation
- [x] Set up database connection and session management
- [x] Implement database utilities (context manager, dependency injection)

## M3 — Core Utilities ✅

- [x] Build configuration loader and validation
- [x] Create business hours and schedule utilities
- [x] Implement Discord webhook client
- [x] Implement LLM API client (unified endpoint)
- [x] Implement SSH client wrapper

## M4 — Services ✅

- [x] Build alert service with Discord integration
- [x] Implement log analyzer with SSH + LLM
- [x] Create internet connectivity monitor
- [x] Build scheduler service (APScheduler)
  - [x] Heartbeat checker (every 1 minute)
  - [x] Log analyzer (every 30 minutes)
  - [x] Database cleanup (daily at 3 AM)
  - [x] Health check (hourly)

## M5 — API & Dashboard ✅

- [x] Implement FastAPI heartbeat endpoints
- [x] Build host management REST API
- [x] Create simple web dashboard (HTML/JS)
- [x] Add health check endpoint

## M6 — Client Tools & Scripts ✅

- [x] Write client heartbeat script (Bash)
- [x] Write host registration script (Python)
- [x] Create setup automation script
- [x] Create example configuration files

## M7 — Documentation ✅

- [x] Write comprehensive README
- [x] Document architecture (ARCHITECTURE.md)
- [x] Document requirements (REQUIREMENTS.md)
- [x] Create troubleshooting guide
- [x] Add inline code documentation

## M7.5 — Container Consolidation & Configuration Management ✅

- [x] Consolidate 3 Docker containers into single container
- [x] Create startup script to manage all services in one container
- [x] Add API endpoint for viewing all configurations (GET /api/v1/hosts/config/all)
- [x] Add API endpoint for quick config updates (PATCH /api/v1/hosts/{host_id}/config)
- [x] Build web-based configuration management UI (/api/v1/config)
- [x] Update documentation for single container architecture
- [x] Update troubleshooting guide with new container name

## M8 — Testing & Validation 🔄 (In Progress)

- [ ] Write unit tests for core utilities
- [ ] Write integration tests for API endpoints
- [ ] Test heartbeat flow end-to-end
- [ ] Test log analysis with real firewall
- [ ] Test internet monitor with healthchecks.io
- [ ] Verify business hours scheduling
- [ ] Load test with 20+ hosts
- [ ] Security audit

## M8.5 — Project-Specific Polling Rollout 🔄 (In Progress)

- [ ] Review per-project monitoring docs (starting with Evie) and capture poll targets
- [ ] Model project services/endpoints in database schema (hosts/config tables)
- [ ] Implement polling job to call project health endpoints on schedule
- [ ] Extend alert service to classify per-project component failures
- [ ] Surface project polling status in dashboard & config UI
- [ ] Document onboarding runbook for adding new projects/services
- [ ] Backfill TASKS/PROJECT_STATUS/STATUS docs after each project onboarding

## M9 — Deployment & Operations (Pending)

- [ ] Deploy to staging environment
- [ ] Configure SSL/TLS (reverse proxy)
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Document operations procedures
- [ ] Create runbooks for common issues

## M10 — Phase 2 Enhancements (Backlog)

- [ ] PostgreSQL migration support
- [ ] Web UI for host management
- [ ] Alert acknowledgment workflow
- [ ] Historical metrics and dashboards
- [ ] Grafana integration
- [ ] CI/CD pipeline

## MVP Completion Status

**Completed**: M1-M7.5 (Foundation through Configuration Management)
**In Progress**: M8 (Testing & Validation)
**Pending**: M9-M10 (Deployment & Phase 2)

**Overall Progress**: 88% MVP complete
