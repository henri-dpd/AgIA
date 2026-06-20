# TypeScript — best practices

## Type system

- Enable `strict` mode in `tsconfig.json`; never disable individual strict flags to silence errors.
- Prefer `interface` for object shapes that can be extended; use `type` for unions, intersections, and mapped types.
- Never use `any`; use `unknown` when the type is genuinely unknown and narrow before use.
- Avoid non-null assertions (`!`) unless unavoidable; prefer explicit null checks.
- Use `readonly` for properties and arrays that must not be mutated after construction.
- Prefer `as const` for literal values instead of widening them to `string` or `number`.

## Functions

- Annotate every parameter and return type explicitly; do not rely on inference for public API signatures.
- Prefer pure functions; avoid side effects in functions named after queries (getters, finders).
- Use overloads sparingly — only when callers need distinct type signatures, not for optional parameters.

## Modules and imports

- Use ES module syntax (`import`/`export`); avoid `require` in new code.
- Group imports: external packages first, then internal modules, then types-only imports (`import type`).
- Re-export types with `export type` to prevent value-import leakage.

## Error handling

- Use typed error classes that extend `Error`; never throw strings or plain objects.
- Prefer discriminated union result types (`{ ok: true; value: T } | { ok: false; error: string }`) for recoverable errors in business logic.
- Always annotate `catch` clauses: `catch (err: unknown)` and narrow before accessing properties.

## Naming conventions

| Entity | Convention | Example |
|---|---|---|
| Variable / function | `camelCase` | `getUserById` |
| Class / interface / type | `PascalCase` | `UserRepository` |
| Enum | `PascalCase` members | `Direction.North` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| File | `kebab-case.ts` | `user-service.ts` |

## Anti-patterns

- Do not use `Function`, `Object`, or `{}` as types.
- Do not cast with `as T` to silence type errors; fix the underlying type issue.
- Do not mix `.js` and `.ts` files in the same compilation unit.
- Do not ignore `@ts-ignore` or `@ts-expect-error` comments without a justification comment on the same line.
