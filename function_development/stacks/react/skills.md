# React — skills

## Core libraries

| Library | Purpose |
|---|---|
| React 18+ | UI rendering |
| React DOM | Browser rendering target |
| React Router v6 | Client-side routing |
| `@tanstack/react-query` | Server state, caching, background refetch |
| Zustand | Lightweight global client state |
| React Hook Form | Form state and validation |
| Zod | Schema validation for form and API data |

## Developer tooling

| Tool | Purpose |
|---|---|
| Vite | Dev server and build |
| Storybook | Component development in isolation |
| MSW (Mock Service Worker) | API mocking in tests and Storybook |
| `@testing-library/react` | DOM-focused component testing |
| Vitest | Test runner |

## Custom hook pattern

```typescript
function useUser(id: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["user", id],
    queryFn: () => fetchUser(id),
  });
  return { user: data, isLoading, error };
}
```

## Context pattern

```typescript
const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
```
