# M.I.N.E.R. Frontend

Minimal, backend-driven UI for the M.I.N.E.R. evidence pipeline. Two screens only:

- **Ingestion Dashboard** (`/dashboard`) — uploads and batch readiness, read live from
  `GET /api/documents/uploads` and `GET /api/documents/batches`.
- **Report Synthesis** (`/reports`) — generates a cited report from indexed evidence
  via `POST /api/reports/generate-job`, polls `GET /api/reports/job/{job_id}`, then
  approves (`POST /api/reports/{id}/approve`) and downloads the DOCX
  (`GET /api/reports/{id}/download.docx`).

There is no mock data and no simulated stream; every number on screen comes from the
FastAPI backend.

## Backend

Set `VITE_API_BASE_URL` (see `src/api/client.ts`); it defaults to `http://localhost:8000`.
The Vite dev server also proxies `/api` to `http://localhost:8000` (see `vite.config.ts`).

## Styling

Tailwind v4 with the CMPDI portal design tokens declared in `src/index.css`
(`@import "tailwindcss"` + `@theme`). The Report Synthesis screen ships its own
scoped CSS in the same file.

## Project structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx                     ← routes: /dashboard, /reports
│   ├── index.css                   ← Tailwind v4 tokens (@theme) + report styles
│   ├── api/
│   │   └── client.ts                REST base URL + apiGet helper
│   ├── layouts/
│   │   └── AppLayout.tsx
│   ├── components/
│   │   └── layout/                  NationalEmblemBar, PortalHeader, NavStrip, Footer
│   └── pages/
│       ├── DashboardPage.tsx
│       └── ReportSynthesisPage.tsx
```

## Run it

```bash
npm install
npm run dev
```

Open the printed URL; `/dashboard` is the default route. Start the backend first so the
data loads.
