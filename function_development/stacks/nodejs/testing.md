# Node.js — testing

## Framework

Use **Vitest** for speed and ES module support; use **Supertest** for HTTP integration tests.

## Unit tests

```typescript
import { describe, it, expect } from "vitest";
import { hashPassword } from "./auth.js";

describe("hashPassword", () => {
  it("returns a non-empty string", async () => {
    const hash = await hashPassword("secret");
    expect(hash).toBeTypeOf("string");
    expect(hash.length).toBeGreaterThan(0);
  });

  it("produces a different hash each call", async () => {
    const a = await hashPassword("secret");
    const b = await hashPassword("secret");
    expect(a).not.toBe(b);
  });
});
```

## HTTP integration tests (Fastify example)

```typescript
import { build } from "../app.js";
import { describe, it, expect, beforeAll, afterAll } from "vitest";

describe("GET /health", () => {
  const app = build();
  beforeAll(() => app.ready());
  afterAll(() => app.close());

  it("returns 200", async () => {
    const response = await app.inject({ method: "GET", url: "/health" });
    expect(response.statusCode).toBe(200);
  });
});
```

## Mocking modules

```typescript
vi.mock("../db.js", () => ({
  db: { user: { findById: vi.fn().mockResolvedValue({ id: "1", name: "Alice" }) } },
}));
```
