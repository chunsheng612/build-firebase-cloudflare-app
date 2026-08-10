# Framework routing and environment reference

Use this file only after `inspect_project.py` identifies the framework. Confirm against the current framework and Cloudflare documentation before changing adapter packages.

| Framework/build | Browser variable prefix | Typical static output | Cloudflare note |
|---|---|---|---|
| Vite (React/Vue/Svelte) | `VITE_` | `dist` | Use Workers static assets; add SPA fallback for client routing. |
| Create React App | `REACT_APP_` | `build` | Use Workers static assets; add SPA fallback for client routing. |
| Astro | `PUBLIC_` | `dist` | Static output can use assets; SSR needs the Cloudflare adapter. |
| SvelteKit | `PUBLIC_` | adapter-dependent | Use the official Cloudflare adapter; do not guess the generated output. |
| Next.js | `NEXT_PUBLIC_` | `out` only with static export | Use OpenNext for SSR/dynamic features; never deploy `.next` as a static directory. |
| Nuxt | `NUXT_PUBLIC_` via runtime config | adapter-dependent | Follow the current Cloudflare/Nitro guide. |
| Plain browser JS | chosen by build tooling | project-defined | Keep config in a dedicated module; avoid runtime string replacement unless necessary. |

## Rendering decision

Determine whether routes require server rendering, server actions, middleware, image optimization, or runtime secrets. If none do, static output is simpler. If any do, use the official Cloudflare framework adapter instead of forcing a static export.

Do not convert SSR to static export merely to simplify deployment unless the user accepts the product tradeoff.

## Firebase module placement

- Put browser SDK initialization in the framework's client-safe source area.
- With SSR, ensure browser-only services are initialized only in the browser.
- Put Admin SDK code in explicitly server-only modules and guard against accidental client imports.
- Prefer a small service layer over importing Firestore directly from every UI component.

## Environment files

Create an example file with names and blank/example values. Put real local values in the framework's ignored local environment file. Verify ignore rules explicitly; do not assume `.env.local` or `.dev.vars` is ignored.

Cloudflare build-time variables must be available while the frontend is built. Worker runtime secrets are not automatically injected into a prebuilt client bundle.
