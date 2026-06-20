# Angular — best practices

## Architecture

- Use the **standalone component** API (Angular 14+); avoid `NgModule` in new code.
- Apply **OnPush** change detection on every component; only switch to `Default` when a third-party library requires it.
- Follow the **feature module pattern**: each domain area lives in its own folder with its own routes, components, services, and store.

## Components

- Keep templates lean; move business logic to services or state management.
- Use the `inject()` function (Angular 14+) instead of constructor injection for services.
- Prefer `@Input({ required: true })` for mandatory props; do not silently handle `undefined` inputs.
- Use `@Output()` with `EventEmitter` for parent communication; prefer `Signal`-based outputs (Angular 17+) in new code.

## Signals and reactivity (Angular 17+)

- Use `signal<T>()` for local state and `computed()` for derived values.
- Use `effect()` sparingly — only for synchronising with external systems (DOM, analytics).
- Prefer `toSignal()` to bridge `Observable` streams into the signal graph.

## State management

- Use **NgRx** for complex global state with many actors.
- Use **NgRx ComponentStore** for self-contained feature state.
- Use **signals** for simple local component state.

## RxJS

- Unsubscribe from all subscriptions; prefer `takeUntilDestroyed()` (Angular 16+) or the `async` pipe.
- Avoid nested `subscribe()` calls; use `switchMap`, `mergeMap`, or `concatMap` instead.
- Use `HttpClient` with typed generics: `this.http.get<User[]>('/api/users')`.

## Naming conventions

| Entity | Convention |
|---|---|
| Component | `PascalCase` + suffix `Component` |
| Service | `PascalCase` + suffix `Service` |
| Directive | `PascalCase` + suffix `Directive` |
| Pipe | `PascalCase` + suffix `Pipe` |
| File | `kebab-case.component.ts` |
| Selector | `app-feature-name` |

## Anti-patterns

- Do not use `any` in Angular service or component code.
- Do not call `subscribe()` in a component without unsubscribing on destroy.
- Do not mutate `@Input()` properties; emit a new value via `@Output()` instead.
- Do not use `document.querySelector` in components; use `@ViewChild` or the Renderer2 API.
