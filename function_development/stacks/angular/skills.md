# Angular — skills

## Core packages

| Package | Purpose |
|---|---|
| `@angular/core` | Framework core, signals |
| `@angular/router` | Client-side routing |
| `@angular/forms` | Reactive and template-driven forms |
| `@angular/common/http` | `HttpClient` for REST calls |
| `@ngrx/store` + `@ngrx/effects` | Global state management |
| `@ngrx/component-store` | Feature-level reactive state |
| `rxjs` | Reactive streams |

## Developer tooling

| Tool | Purpose |
|---|---|
| Angular CLI (`ng`) | Scaffold, build, serve, test |
| ESLint `@angular-eslint` | Angular-aware lint rules |
| Prettier | Formatting |
| Karma + Jasmine | Default unit test runner |
| Jest (via `jest-preset-angular`) | Faster alternative to Karma |
| Cypress / Playwright | End-to-end testing |

## Signal-based component example

```typescript
@Component({
  selector: "app-counter",
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<p>{{ count() }}</p><button (click)="increment()">+</button>`,
})
export class CounterComponent {
  count = signal(0);
  increment() { this.count.update(v => v + 1); }
}
```

## HTTP with typed response

```typescript
@Injectable({ providedIn: "root" })
export class UserService {
  private http = inject(HttpClient);

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>("/api/users");
  }
}
```
