# goodmap-frontend

Frontend for [GoodMap](https://github.com/Problematy/goodmap). This directory
is part of the `goodmap` monorepo — the backend lives at the repo root, and
this build is bundled into the published `goodmap` PyPI package (see
`make build-frontend` at the repo root).

# Development

To build and run a static version of just the frontend, from this directory:

1. `npm install` -- install all the dependencies,
2. building:
   - `npm run build` -- production build,
   - `npm run dev-build` -- development build,
3. `npm run serve:local` -- run the development server.

To build the frontend the way the backend release does (bundled into
`goodmap/static/frontend/`), run `make build-frontend` from the repo root
instead.
