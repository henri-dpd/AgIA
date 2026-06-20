# React — testing

## Framework

Use **Vitest** + **`@testing-library/react`** + **`@testing-library/user-event`**.

## What to test

- Component renders the correct output for each prop combination.
- User interactions (clicks, typing, form submission) trigger the expected side effects.
- Loading, error, and empty states are handled.
- Custom hooks return the correct values and trigger re-renders on state changes.

## Example component test

```typescript
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("renders the label", () => {
    render(<Button onClick={vi.fn()}>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

## Example hook test

```typescript
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "./useCounter";

it("increments the count", () => {
  const { result } = renderHook(() => useCounter(0));
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});
```

## Mocking API calls

Use **MSW** handlers to intercept network requests:

```typescript
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

server.use(
  http.get("/api/users/:id", () => HttpResponse.json({ id: "1", name: "Alice" }))
);
```
