# JavaScript — skills

## Core tooling

| Tool | Purpose |
|---|---|
| Node.js | Runtime for server-side JS |
| ESLint | Linting (`eslint-config-airbnb-base` or `eslint:recommended`) |
| Prettier | Formatting |
| Jest / Vitest | Unit testing |
| Babel | Transpilation for older targets |

## Useful built-in APIs

| API | Use case |
|---|---|
| `Array.from` | Convert iterables to arrays |
| `Object.entries` / `Object.fromEntries` | Iterate and rebuild objects |
| `structuredClone` | Deep copy without third-party libraries |
| `AbortController` | Cancel async operations (fetch, timers) |
| `crypto.randomUUID()` | Generate RFC 4122 UUIDs natively (Node 19+, browsers) |

## Package.json scripts baseline

```json
{
  "scripts": {
    "lint": "eslint src/",
    "format": "prettier --write src/",
    "test": "jest --coverage",
    "build": "tsc --noEmit"
  }
}
```

## Module patterns

### Named exports (preferred)

```javascript
export function add(a, b) { return a + b; }
```

### Default export (use only for a single primary export per file)

```javascript
export default class UserService { ... }
```
