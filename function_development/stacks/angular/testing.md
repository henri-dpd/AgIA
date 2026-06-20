# Angular — testing

## Unit tests (Karma / Jest)

```typescript
import { TestBed } from "@angular/core/testing";
import { UserService } from "./user.service";
import { HttpTestingController, provideHttpClientTesting } from "@angular/common/http/testing";
import { provideHttpClient } from "@angular/common/http";

describe("UserService", () => {
  let service: UserService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(UserService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it("fetches users", () => {
    service.getUsers().subscribe(users => expect(users.length).toBe(1));
    http.expectOne("/api/users").flush([{ id: "1", name: "Alice" }]);
  });
});
```

## Component tests

```typescript
it("renders user name", () => {
  const fixture = TestBed.createComponent(UserCardComponent);
  fixture.componentRef.setInput("user", { id: "1", name: "Alice" });
  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).toContain("Alice");
});
```

## Signal testing

```typescript
it("increments the count signal", () => {
  const fixture = TestBed.createComponent(CounterComponent);
  fixture.componentInstance.increment();
  expect(fixture.componentInstance.count()).toBe(1);
});
```

## End-to-end (Playwright)

```bash
npx playwright test
```
