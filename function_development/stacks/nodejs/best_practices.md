# Node.js — best practices

## Runtime and modules

- Use **Node.js LTS** (currently 20.x); pin the version in `.nvmrc` and `engines` in `package.json`.
- Use **ES modules** (`"type": "module"` in `package.json`) for new projects; use TypeScript with `"module": "NodeNext"`.
- Avoid CommonJS `require` in new code; use dynamic `import()` where lazy loading is needed.

## Async patterns

- Use `async`/`await` throughout; avoid raw callback APIs unless wrapping a legacy interface.
- Use `util.promisify` to wrap Node.js callback-style APIs.
- Always handle promise rejections; use `process.on("unhandledRejection", ...)` as a last resort catch, not as normal error handling.

## Error handling

- Use typed error classes that extend `Error`.
- Centralise error handling in a middleware layer; do not scatter `try/catch` blocks across route handlers.
- Attach `statusCode` and `isOperational` flags to distinguish operational errors from programming errors.

## Environment and configuration

- Store configuration in environment variables; use `dotenv` or `@fastify/env` for local development.
- Validate environment variables at startup with Zod; fail fast if required variables are missing.
- Never hard-code secrets; never commit `.env` files.

## Performance

- Use the `cluster` module or a process manager (PM2) to utilise multiple CPU cores.
- Stream large responses and file operations; avoid loading large payloads into memory.
- Use `worker_threads` for CPU-bound tasks to avoid blocking the event loop.

## Security

- Keep dependencies updated; run `npm audit` in CI.
- Sanitise all user input before using it in database queries, shell commands, or file paths.
- Set security headers with `helmet` when running an HTTP server.
- Rate-limit public endpoints.

## Naming conventions

| Entity | Convention |
|---|---|
| File | `kebab-case.ts` |
| Class / interface | `PascalCase` |
| Function / variable | `camelCase` |
| Constant | `SCREAMING_SNAKE_CASE` |
| Environment variable | `SCREAMING_SNAKE_CASE` |

## Anti-patterns

- Do not use `setTimeout` for retries; use a library like Polly or `p-retry`.
- Do not use synchronous fs methods (`readFileSync`) in request handlers.
- Do not ignore the `error` event on streams; it causes unhandled exceptions.
- Do not use `__dirname` in ES modules; use `import.meta.dirname` (Node 21.2+) or `fileURLToPath`.
