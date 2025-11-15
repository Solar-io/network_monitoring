# App Frameworks (Web)

Recommendation
- Next.js (App Router) + React Server Components + Edge/Node runtimes
  - Pros: streaming UI (Server Actions), file-based routing, SSR/ISR, solid DX.
  - Cons: RSC learning curve; careful client/server boundary management.

Alternatives
- SvelteKit: small, fast, great ergonomics; smaller ecosystem than React.
- Remix: good for nested routing and web fundamentals; fewer AI-first examples.
- Astro (islands): content-heavy sites; pair with API routes for AI endpoints.

Runtime & Infra
- Node.js 20+ (or Bun 1.1+); Vercel/Netlify for serverless/edge or self-host.
- WebSockets/Server-Sent Events for streaming; tRPC or REST for typed APIs.
- Storage: SQLite by default (single-user portability); optional Postgres later. Redis optional. Local FS for files; optional vector DB.

Recommended Stack
- Next.js + React + Tailwind + shadcn/ui + Radix + TanStack Query.
- LangGraph/LangChain or custom agent framework as needed.

POC Checklist
- Streamed assistant responses from server.
- Tool calls with server-side execution + UI traces.
- Sub-agent orchestration endpoint with run IDs.

Next.js Project Layout (App Router)
- app/
  - layout.tsx, page.tsx
  - api/
    - chat/route.ts (POST — orchestrate)
    - stream/route.ts (GET — SSE for streaming tokens)
    - tools/[name]/route.ts (POST — tool execution)
- lib/
  - orchestrator.ts, agents/
  - tracing.ts, sse.ts, schema.ts
- components/
  - chat, composer, run-panel, agent-picker, template-library

Streaming Endpoints
- SSE (server): emit event types `token`, `event`, `error`, `done` with `runId`.
- WebSocket (optional): for bi-directional tool UIs.

Caching & Data
- App DB (SQLite default): threads, messages, runs, events, artifacts.
- Redis: ephemeral runs, rate limits, queues.
- Vector store: pgvector, Qdrant, Weaviate, or Pinecone for long-term memory.

Runtimes
- Edge where practical for latency; Node runtime for tool execution requiring local FS or shell access.

Bootstrap (Next.js + Tailwind + shadcn/ui)
- Create app:
  - `npx create-next-app@latest my-ai-app --ts --eslint --src-dir --app --import-alias "@/*"`
- Add Tailwind:
  - `cd my-ai-app && npx tailwindcss init -p`
  - Configure `tailwind.config.js` content to include `./src/**/*.{ts,tsx}` and add Radix/shadcn presets.
- Install shadcn/ui:
  - `npm i tailwind-merge class-variance-authority lucide-react` (or heroicons if chosen)
  - `npx shadcn-ui@latest init`
  - `npx shadcn-ui@latest add button input textarea dialog dropdown-menu toast` (add as needed)
- Add Radix Primitives as needed: `npm i @radix-ui/react-dialog @radix-ui/react-dropdown-menu`
- Wire initial pages: chat (stream), run panel, agent picker, settings.
- Configure environment: copy `.env.example` to `.env` and set keys.
- Commit and snapshot: `scripts/snapshot.sh "bootstrap nextjs+tailwind+shadcn"`
