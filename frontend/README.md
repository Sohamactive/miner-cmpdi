# M.I.N.E.R. Frontend — AI Query & Topic Explorer (scoped build)

This build implements two of the five M.I.N.E.R. screens end-to-end, per request:

- **AI Query & Evidence Viewer** (`/ai-query`) — default route
- **Topic Explorer & Clusters** (`/topics`)

Dashboard & Ingestion, Human Review & Approval, and Report Synthesis are **excluded**
from this build. Their nav tabs still render (to keep the full information
architecture visible) but are disabled/unlinked rather than routed.

You can jump between the two implemented screens in either direction:
- **AI Query → Topics**: "View topic clusters" link next to Extracted Context Vectors.
- **Topics → AI Query**: "Load in AI Reader" on any archive card.

## Real-time generation over WebSockets

The "Synthesize" action does not wait for one big response. It opens a
WebSocket to `VITE_WS_BASE_URL + /ws/query`, sends `{ type: "query", query, filters }`,
and renders every event the backend pushes back as it arrives:

```
status   → orchestrator stage label (e.g. "Retrieving vectors from Qdrant index")
token    → next chunk of the answer text (renders immediately, with a live caret)
vector   → one retrieved context vector (renders into "Extracted Context Vectors")
citation → one inline citation reference
evidence → the grounded source document (renders the right-hand document viewer)
borehole → corroborating borehole logs
seams    → seam thickness table rows
done     → generation finished
error    → surfaced inline, stream stops
```

See `src/types/index.ts` (`QueryStreamEvent`) for the exact shape and
`src/hooks/useAIQueryStream.ts` for the client-side reducer.

**No backend required to demo.** If the socket doesn't open within 1.2s (no
backend running, or `VITE_WS_BASE_URL` unset), the hook automatically falls
back to a scripted local timeline (`src/data/mockData.ts`) that emits the same
event shape, so the full streaming experience — token-by-token synthesis,
vectors populating, the evidence panel and borehole logs appearing — is
visible standalone. A small "· local simulation" label appears in the
telemetry panel whenever this fallback is active.

To connect a real backend, implement a WebSocket endpoint at `/ws/query` that
accepts the query payload and pushes `QueryStreamEvent` JSON frames, then set
`VITE_WS_BASE_URL` (see `.env.example`).

## Project structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── .env.example
├── public/
├── src/
│   ├── main.tsx
│   ├── App.tsx                     ← only /ai-query and /topics are routed
│   ├── index.css                   ← Tailwind v4 tokens (@theme)
│   ├── api/
│   │   ├── client.ts                REST/WS base URL config
│   │   ├── query.ts                 WS URL + outbound payload builder
│   │   └── topics.ts                 topic bundle fetch (mock-backed for now)
│   ├── hooks/
│   │   └── useAIQueryStream.ts       WebSocket client + local fallback simulator
│   ├── layouts/
│   │   └── AppLayout.tsx
│   ├── components/
│   │   ├── layout/                   NationalEmblemBar, PortalHeader, NavStrip, Sidebar, Footer
│   │   └── ui/                       Badge, Button, SearchInput, FilterPills, TopicCard,
│   │                                  TopicChip, StreamingText, ConfidenceMeter
│   ├── pages/
│   │   ├── AIQueryPage.tsx
│   │   └── TopicExplorerPage.tsx
│   ├── data/
│   │   └── mockData.ts               seed data + scripted WS event timeline
│   ├── types/
│   │   └── index.ts
│   └── lib/
│       └── cn.ts
```

## Run it

```bash
npm install
npm run dev
```

Opens at `/ai-query`. Type a query and hit **Synthesize** — no backend needed
to see the full streamed experience.
