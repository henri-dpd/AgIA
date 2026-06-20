# Next.js — workflow

## Step 1 — Clarify rendering strategy

- Static (SSG) → no dynamic data, can be prerendered at build time.
- Dynamic (SSR / PPR) → data changes per request.
- Client → user interaction requires browser APIs.

## Step 2 — Create the route

```
app/
  (dashboard)/
    users/
      page.tsx        ← Server Component
      loading.tsx     ← Suspense boundary UI
      error.tsx       ← Error boundary UI
      [id]/
        page.tsx
```

## Step 3 — Fetch data in the Server Component

```typescript
// app/users/page.tsx
export default async function UsersPage() {
  const users = await db.user.findMany();
  return <UserList users={users} />;
}
```

## Step 4 — Add client interactivity

- Add `"use client"` to the smallest sub-tree that needs it.
- Pass serialisable props from Server to Client Components; do not pass functions or class instances.

## Step 5 — Handle mutations with Server Actions

```typescript
// app/users/actions.ts
"use server";
export async function createUser(data: FormData) {
  const parsed = CreateUserSchema.safeParse(Object.fromEntries(data));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.user.create({ data: parsed.data });
  revalidatePath("/users");
}
```

## Step 6 — Review checklist

- [ ] Server Components have no `"use client"` directive.
- [ ] All user inputs validated with Zod in Server Actions.
- [ ] Images use `next/image`; fonts use `next/font`.
- [ ] No secrets in `NEXT_PUBLIC_` variables.
- [ ] `error.tsx` and `loading.tsx` present for data-fetching routes.
