# React + Vite

## Local demonstration mode

`npm run dev` starts the site in local demo mode by default. The dashboard, sample job
postings, candidate profile, repositories, skill-gap assessment, evidence examples, and
15-day roadmap are loaded from `src/data/demoData.js`; this does not seed or modify the
backend database. Demo repositories are placeholders and are not authenticated, scanned,
or verified against GitHub. Demo assessment excerpts and scores are illustrative only.

To use the live FastAPI backend while developing, set `VITE_DEMO_MODE=false` in the
frontend environment and start the backend separately. `VITE_API_BASE_URL` can override
the default `http://127.0.0.1:8000/api/v1` API URL. Demo mode is not enabled by default
in production builds; set `VITE_DEMO_MODE=true` only when intentionally publishing a
demonstration build.

Run the frontend checks with `npm test`, `npm run lint`, and `npm run build`.

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
