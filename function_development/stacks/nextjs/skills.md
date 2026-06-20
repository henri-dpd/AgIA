# Next.js — skills

## Core stack

| Package | Purpose |
|---|---|
| `next` | Framework |
| `react` + `react-dom` | UI rendering |
| `typescript` | Type safety |
| `zod` | Schema validation |
| `@prisma/client` | Database ORM (common choice) |
| `next-auth` | Authentication |

## Developer tooling

| Tool | Purpose |
|---|---|
| `next dev --turbo` | Fast local dev server with Turbopack |
| ESLint `eslint-config-next` | Next.js-aware lint rules |
| Prettier | Formatting |
| Playwright | End-to-end testing |
| Vitest + Testing Library | Unit and integration testing |

## Key config options in `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    ppr: true,           // Partial Prerendering
    serverActions: { allowedOrigins: ["example.com"] },
  },
  images: {
    remotePatterns: [{ hostname: "cdn.example.com" }],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
    ];
  },
};
export default nextConfig;
```

## Middleware pattern

```typescript
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("session")?.value;
  if (!token) return NextResponse.redirect(new URL("/login", request.url));
  return NextResponse.next();
}
export const config = { matcher: ["/dashboard/:path*"] };
```
