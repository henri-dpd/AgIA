# TypeScript — skills

## Core tooling

| Tool | Purpose | Config file |
|---|---|---|
| TypeScript compiler (`tsc`) | Type checking and transpilation | `tsconfig.json` |
| ESLint + `@typescript-eslint` | Linting | `.eslintrc.json` |
| Prettier | Formatting | `.prettierrc` |
| Jest / Vitest | Unit testing | `jest.config.ts` / `vitest.config.ts` |
| ts-node | Run `.ts` files directly | — |

## Recommended `tsconfig.json` baseline

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": false,
    "outDir": "dist"
  },
  "include": ["src"]
}
```

## Utility types to know

| Type | When to use |
|---|---|
| `Partial<T>` | Optional version of T for update payloads |
| `Required<T>` | All properties mandatory |
| `Readonly<T>` | Immutable version |
| `Pick<T, K>` | Subset of T |
| `Omit<T, K>` | T without keys K |
| `Record<K, V>` | Typed map / dictionary |
| `ReturnType<F>` | Infer the return type of a function |
| `Parameters<F>` | Infer parameter types as a tuple |

## Common patterns

### Discriminated unions for results

```typescript
type Result<T, E = string> =
  | { ok: true; value: T }
  | { ok: false; error: E };
```

### Exhaustiveness check

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}
```

### Typed event emitter

Use `EventEmitter<{ eventName: [payload] }>` from the `typed-emitter` package rather than the untyped Node.js one.
