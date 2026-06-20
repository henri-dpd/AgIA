# TypeScript — testing

## Framework choice

| Framework | When to choose |
|---|---|
| **Vitest** | New projects, Vite-based toolchains, fast watch mode |
| **Jest** + `ts-jest` | Legacy codebases already using Jest |

## Test file conventions

- Colocate test files next to source files: `user-service.test.ts` beside `user-service.ts`.
- Name tests with the pattern `describe('functionName') > it('should <behaviour> when <condition>')`.
- Use `beforeEach` to reset state; avoid shared mutable state across `it` blocks.

## Type-level testing

Use `expectTypeOf` (Vitest) or `@type-challenges/utils` to assert inferred types do not regress:

```typescript
import { expectTypeOf } from "vitest";
expectTypeOf(normalize).returns.toEqualTypeOf<number[]>();
```

## Mocking

- Prefer dependency injection over module-level mocks.
- Use `vi.fn()` (Vitest) or `jest.fn()` for function mocks; always type the mock: `vi.fn<[number], string>()`.
- Avoid `jest.mock()` for local modules when a simple stub object suffices.

## Coverage

- Aim for 100 % branch coverage on pure utility functions.
- Skip coverage for trivial getters; focus on business logic branches.

## Example test structure

```typescript
import { describe, it, expect } from "vitest";
import { normalizeScores } from "./normalize-scores";

describe("normalizeScores", () => {
  it("scales values to [0, 1] range", () => {
    expect(normalizeScores([0, 50, 100])).toEqual([0, 0.5, 1]);
  });

  it("throws RangeError for an empty list", () => {
    expect(() => normalizeScores([])).toThrow(RangeError);
  });

  it("throws RangeError when all values are equal", () => {
    expect(() => normalizeScores([5, 5, 5])).toThrow(RangeError);
  });
});
```
