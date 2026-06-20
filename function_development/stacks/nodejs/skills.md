# Node.js — skills

## Core built-in modules

| Module | Common use |
|---|---|
| `fs/promises` | File I/O |
| `path` | Path manipulation |
| `stream` / `stream/promises` | Streaming data |
| `http` / `https` | Low-level HTTP server |
| `crypto` | Hashing, HMAC, UUID |
| `worker_threads` | CPU-bound parallelism |
| `child_process` | Shell commands (use carefully) |

## Frequently used packages

| Package | Purpose |
|---|---|
| `fastify` or `express` | HTTP framework |
| `zod` | Schema validation |
| `pino` | Structured logging |
| `drizzle-orm` / `prisma` | Database ORM |
| `vitest` | Testing |
| `tsx` | TypeScript execution without build |
| `dotenv` | Local `.env` loading |
| `helmet` | HTTP security headers |

## Structured logging with Pino

```typescript
import pino from "pino";
export const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });
logger.info({ userId: "123" }, "User signed in");
```

## Graceful shutdown

```typescript
process.on("SIGTERM", async () => {
  logger.info("SIGTERM received — shutting down");
  await server.close();
  await db.end();
  process.exit(0);
});
```
