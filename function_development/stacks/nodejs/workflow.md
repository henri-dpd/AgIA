# Node.js — workflow

## Step 1 — Initialise the project

```bash
npm init -y
npm install typescript @types/node tsx --save-dev
npx tsc --init
```

Set `"type": "module"` in `package.json` and configure `tsconfig.json` for `NodeNext` modules.

## Step 2 — Validate environment at startup

```typescript
import { z } from "zod";
const Env = z.object({ PORT: z.coerce.number().default(3000), DATABASE_URL: z.string().url() });
export const env = Env.parse(process.env);
```

## Step 3 — Implement

- Structure code with `src/` for source, `dist/` for compiled output.
- Use async functions throughout; handle errors at the boundary layer.

## Step 4 — Lint and test

```bash
npx eslint src/
npx vitest run
```

## Step 5 — Build and start

```bash
npx tsc --noEmit   # type check
node --import tsx/esm src/index.ts   # local dev
```

## Step 6 — Review checklist

- [ ] Environment variables validated with Zod at startup.
- [ ] No synchronous I/O in request paths.
- [ ] All streams have error event handlers.
- [ ] Security headers set (helmet or equivalent).
- [ ] `npm audit` passes with no critical vulnerabilities.
