# Next.js — testing

## Strategy

| Layer | Tool |
|---|---|
| Unit (utilities, hooks) | Vitest + Testing Library |
| Integration (Server Components, actions) | Vitest with mocked DB |
| End-to-end | Playwright |

## Testing Server Components

```typescript
// app/users/page.test.tsx
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import UsersPage from "./page";

vi.mock("@/lib/db", () => ({
  db: { user: { findMany: vi.fn().mockResolvedValue([{ id: "1", name: "Alice" }]) } },
}));

it("renders a list of users", async () => {
  render(await UsersPage());
  expect(screen.getByText("Alice")).toBeInTheDocument();
});
```

## Testing Server Actions

```typescript
import { createUser } from "./actions";
import { db } from "@/lib/db";
import { vi } from "vitest";

vi.mock("@/lib/db");

it("creates a user from valid FormData", async () => {
  const form = new FormData();
  form.append("name", "Bob");
  form.append("email", "bob@example.com");
  const result = await createUser(form);
  expect(result).toBeUndefined();
  expect(db.user.create).toHaveBeenCalled();
});
```

## Playwright end-to-end example

```typescript
import { test, expect } from "@playwright/test";

test("user can sign in", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="email"]', "alice@example.com");
  await page.fill('[name="password"]', "secret");
  await page.click('[type="submit"]');
  await expect(page).toHaveURL("/dashboard");
});
```
