# TypeScript — workflow

## Step 1 — Understand the requirement

- Read the function specification and identify the input/output types.
- Map each domain concept to a TypeScript type or interface before writing code.
- Identify edge cases: `null`/`undefined` inputs, empty arrays, boundary values.

## Step 2 — Design types first

- Define all input and output types as `interface` or `type` aliases.
- Check whether the types must be exported for callers or kept internal.
- If a function can fail, decide between throwing, returning a discriminated union, or returning `undefined`.

## Step 3 — Implement with strict mode

- Run `tsc --noEmit` incrementally; fix all errors before committing.
- Prefer functional transformations (`map`, `filter`, `reduce`) over imperative loops for collections.
- Annotate async functions with `Promise<T>` return types; never leave them as `Promise<any>`.

## Step 4 — Lint and format

```bash
npx eslint --fix src/
npx prettier --write src/
```

## Step 5 — Test

- Run tests with `npx jest` or `npx vitest run`.
- Add at least one test per documented edge case.
- Confirm type coverage is not reduced by the new code.

## Step 6 — Review checklist

- [ ] `strict` mode is on and no new suppressions added.
- [ ] All public functions have explicit return types.
- [ ] Error handling uses typed error classes or discriminated unions.
- [ ] No `any`, `Function`, or `Object` in the changed files.
- [ ] Tests cover the happy path and at least two edge cases.
