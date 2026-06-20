# JavaScript — testing

## Framework

- Use **Vitest** for new projects; **Jest** for existing codebases.
- Place test files next to source files: `user-service.test.js`.

## Patterns

```javascript
import { describe, it, expect, vi } from "vitest";
import { add } from "./math.js";

describe("add", () => {
  it("returns the sum of two numbers", () => {
    expect(add(2, 3)).toBe(5);
  });

  it("handles negative numbers", () => {
    expect(add(-1, 1)).toBe(0);
  });
});
```

## Mocking

- Use `vi.fn()` / `jest.fn()` for function mocks.
- Use `vi.spyOn` / `jest.spyOn` to wrap existing functions without replacing them.
- Reset mocks between tests with `beforeEach(() => vi.clearAllMocks())`.

## Async tests

```javascript
it("resolves with user data", async () => {
  const user = await fetchUser(1);
  expect(user.id).toBe(1);
});

it("rejects when user not found", async () => {
  await expect(fetchUser(-1)).rejects.toThrow("Not found");
});
```

## Coverage

- Run `vitest run --coverage` to generate an Istanbul report.
- Aim for full branch coverage on pure functions.
