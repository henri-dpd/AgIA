# Angular — workflow

## Step 1 — Scaffold

```bash
ng generate component features/users/user-list --standalone
ng generate service features/users/user
ng generate pipe shared/pipes/truncate --standalone
```

## Step 2 — Implement with OnPush

- Set `changeDetection: ChangeDetectionStrategy.OnPush` on every new component.
- Use signals for local state; derive computed values with `computed()`.

## Step 3 — Wire routing

```typescript
// app.routes.ts
export const routes: Routes = [
  {
    path: "users",
    loadComponent: () => import("./features/users/user-list.component").then(m => m.UserListComponent),
  },
];
```

## Step 4 — Lint and format

```bash
ng lint
npx prettier --write src/
```

## Step 5 — Test

```bash
ng test --watch=false --browsers=ChromeHeadless
```

## Step 6 — Review checklist

- [ ] Every component uses `OnPush` change detection.
- [ ] All `Observable` subscriptions are unsubscribed.
- [ ] Standalone components; no `NgModule` in new files.
- [ ] No `any` in component or service code.
- [ ] Unit tests cover the component logic and service calls.
