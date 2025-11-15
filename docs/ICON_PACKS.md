# Icon Packs

Recommendations
- Lucide: open-source, consistent stroke icons, tree-shakable.
- Radix Icons: pairs well with Radix/shadcn.
- Heroicons: great defaults for Tailwind ecosystems.
- Phosphor: broad set, multiple weights.
- Font Awesome: huge catalog; requires license for Pro; familiar.
- Streamline: very comprehensive; commercial license.
- React Icons: wrapper exposing many packs via one interface.
- Feather Icons: lightweight, simple strokes.
- Iconify: meta-pack with many icon sets and on-demand loading.

Guidelines
- Standardize size (e.g., 16/20/24) and stroke width.
- Name by semantic purpose (e.g., `run`, `stop`, `agent`, `tool`, `memory`).
- Wrap icons in a single `<Icon name="..." />` with a mapping to packs.
- Prefer outlined icons; reserve filled for emphasis or active states.

Examples
- Success: `Icon name="agent"` → lucide `bot`
- Warning: `Icon name="rate-limit"` → lucide `gauge`

Semantic Mapping (starter)
- agent → lucide:bot
- tool → lucide:wrench
- orchestrate → lucide:sitemap
- research → lucide:search
- code → lucide:code-2
- test → lucide:beaker
- run → lucide:play
- stop → lucide:square
- retry → lucide:rotate-ccw
- stream → lucide:waves
- link → lucide:link
- copy → lucide:copy
- share → lucide:share-2
- cost → lucide:coin
- latency → lucide:timer
- token → lucide:box

Fallback Policy
- Prefer Lucide; if missing, fallback via React Icons to compatible alternatives.

Project Selection
- Configure default `icon_pack` in `config/project.yml` (supported: heroicons, fontawesome, streamline, react-icons, phosphor, feather, iconify, lucide, radix-icons).
