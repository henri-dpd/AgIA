# JavaScript — workflow

## Step 1 — Understand the requirement

- Identify all inputs, outputs, and error conditions from the specification.
- Note any environment constraints (browser, Node.js, Deno, edge runtime).

## Step 2 — Implement

- Use ES module syntax unless a specific CommonJS target is required.
- Apply `const` for all values that do not change; use `let` only when necessary.
- Handle errors explicitly with `try/catch` or rejected promise handling.

## Step 3 — Lint and format

```bash
npx eslint --fix src/
npx prettier --write src/
```

## Step 4 — Test

```bash
npx jest
# or
npx vitest run
```

## Step 5 — Review checklist

- [ ] No `var` declarations.
- [ ] No `==` or `!=` comparisons.
- [ ] All async paths have error handling.
- [ ] No unused variables or imports.
- [ ] Tests cover the happy path and key edge cases.
