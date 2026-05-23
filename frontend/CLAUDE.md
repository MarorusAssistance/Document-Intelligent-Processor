# frontend/CLAUDE.md

Frontend-specific rules. See repo root `CLAUDE.md` first.

## Stack

Next.js 15 (App Router) · TypeScript strict · Tailwind 4 · shadcn/ui · MSAL for Entra External ID.

## Layout

```
src/
├── app/            App Router. Route groups: (auth)/ for protected pages.
├── components/
│   ├── ui/         shadcn primitives (generated)
│   └── features/   Domain components
├── lib/            api-client.ts, auth.ts, env.ts (zod-validated), utils.ts
├── types/          api.generated.ts — generated from OpenAPI, gitignored
└── hooks/
```

## Hard rules

- App Router only. No Pages Router.
- Types in `types/api.generated.ts` regenerated in `npm run build` from `../docs/api/openapi.json`. Never edit by hand.
- `env.ts` validates env vars with zod at boot. Fail fast.
- File names: `kebab-case.tsx`. Components: `PascalCase`. Variables/functions: `camelCase`.
- No BFF in `app/api/` unless explicitly justified.
- No `localStorage` for sensitive data — MSAL handles tokens.
