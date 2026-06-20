# JavaScript — best practices

## Language version

- Target ES2022+ unless the deployment environment dictates otherwise.
- Use ES modules (`import`/`export`) in new code; avoid `require` except in legacy CommonJS contexts.
- Enable `"use strict"` in every CommonJS file that cannot use ES modules.

## Variables

- Use `const` by default; use `let` only when reassignment is required; never use `var`.
- Declare one variable per `const`/`let` statement for readability.

## Functions

- Prefer arrow functions for callbacks and inline expressions.
- Use named function declarations for top-level functions to aid stack traces.
- Avoid the `arguments` object; use rest parameters (`...args`) instead.

## Null and undefined

- Use strict equality (`===`/`!==`) for all comparisons; never rely on type coercion.
- Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual null guards.
- Treat `undefined` (missing) and `null` (intentionally absent) as distinct concepts.

## Error handling

- Always throw `Error` instances, not strings or plain objects.
- Use `instanceof` to check error types; never inspect `err.message` for branching logic.
- Handle promise rejections explicitly; do not leave unhandled `Promise` chains.

## Async code

- Prefer `async`/`await` over raw `.then()`/`.catch()` chains.
- Use `Promise.all` for independent concurrent operations; use `Promise.allSettled` when partial failure is acceptable.
- Always `await` in a `try/catch` block; never swallow errors silently.

## Naming conventions

| Entity | Convention | Example |
|---|---|---|
| Variable / function | `camelCase` | `fetchUser` |
| Constructor / class | `PascalCase` | `UserService` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| File | `kebab-case.js` | `user-service.js` |

## Anti-patterns

- Do not use `==` or `!=` for any comparison.
- Do not use `eval`, `Function()`, or `with`.
- Do not modify built-in prototypes.
- Do not rely on implicit global variables; always declare with `const`/`let`.
