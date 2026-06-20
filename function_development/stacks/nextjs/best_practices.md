# Next.js — best practices

## Routing and rendering

- Use the **App Router** (`app/`) in new projects; migrate Pages Router (`pages/`) code to App Router incrementally.
- Default to **Server Components**; add `"use client"` only when a component needs browser APIs, event handlers, or React hooks.
- Use **Server Actions** for form mutations; avoid writing separate API route handlers for mutations triggered by forms.

## Data fetching

- Fetch data directly in Server Components using `fetch` with caching semantics (`cache: "force-cache"`, `next: { revalidate }`, or `cache: "no-store"`).
- Use **React Query** or **SWR** only for client-side data that requires real-time updates or user-triggered refetches.
- Co-locate data-fetching functions with the components that use them; do not centralise all fetchers in a single file.

## Performance

- Use `next/image` for all images; never use a bare `<img>` tag.
- Use `next/font` for web fonts to avoid layout shift.
- Use `next/link` for all internal navigation; never use `<a>` tags for internal routes.
- Enable partial prerendering (PPR) for pages that mix static and dynamic content.

## Error handling

- Use `error.tsx` boundaries at the route segment level to contain failures.
- Use `not-found.tsx` for 404 responses instead of redirecting to a generic error page.
- Wrap Server Action calls in `try/catch` and return typed error objects; do not throw HTTP errors to the client.

## Security

- Validate and sanitise all user inputs on the server (Server Actions or Route Handlers) using Zod.
- Never expose environment variables prefixed without `NEXT_PUBLIC_` to the client bundle.
- Set `Content-Security-Policy` and other security headers in `next.config.js` `headers()`.

## Naming conventions

| Entity | Convention |
|---|---|
| Page file | `page.tsx` (reserved) |
| Layout file | `layout.tsx` (reserved) |
| Loading UI | `loading.tsx` (reserved) |
| Error boundary | `error.tsx` (reserved) |
| Server Action file | `actions.ts` |
| API Route Handler | `route.ts` (reserved) |

## Anti-patterns

- Do not use `getServerSideProps` or `getStaticProps` in the App Router; use async Server Components instead.
- Do not add `"use client"` to layout files; keep layouts as Server Components and push the boundary down.
- Do not store secrets in `NEXT_PUBLIC_` environment variables.
