# React — best practices

## Components

- Write **functional components** exclusively; class components are legacy.
- Keep components focused on a single responsibility; split when a component renders more than one distinct concern.
- Co-locate a component with its styles and tests: `Button/Button.tsx`, `Button/Button.test.tsx`, `Button/Button.module.css`.

## Props

- Define props with a named `interface` or `type`; never use `any` or `React.FC` with implicit children.
- Mark props that represent events with the `on` prefix: `onChange`, `onSubmit`.
- Use `children: React.ReactNode` for slots; use render props only when multiple slots are required.

## State management

- Use `useState` for local UI state; `useReducer` when state transitions are complex or interdependent.
- Use context (`useContext`) only for truly global state (theme, locale, auth); do not use it as a substitute for prop drilling on two levels.
- For server state, prefer **React Query** (`@tanstack/react-query`) or **SWR** over manual `useEffect` + `useState` data-fetching.

## Side effects

- Every `useEffect` must have a dependency array; an empty array `[]` is intentional only for mount-once effects.
- Cancel async operations started in `useEffect` with a cleanup function using `AbortController`.
- Do not fetch data inside `useEffect` in new code; use a data-fetching library instead.

## Performance

- Wrap expensive computations with `useMemo`; wrap callback props with `useCallback` only when passed to memoised children.
- Use `React.memo` on leaf components that receive stable props and re-render frequently.
- Avoid anonymous object literals and arrow functions in JSX props that cause unnecessary re-renders.

## Accessibility

- Every interactive element must be reachable by keyboard and have a descriptive label.
- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`); do not use `<div onClick>` for interactive controls.
- Provide `alt` text for every `<img>`; use `alt=""` for decorative images.

## Naming conventions

| Entity | Convention |
|---|---|
| Component | `PascalCase` — `UserCard` |
| Hook | `use` prefix — `useUser` |
| Event handler | `handle` prefix — `handleSubmit` |
| Context | `PascalCase` + `Context` — `AuthContext` |

## Anti-patterns

- Do not mutate state directly; always create a new reference.
- Do not derive state from props on every render; memoize or lift state instead.
- Do not use indexes as `key` in dynamic lists that can reorder.
- Do not read from the DOM with `document.querySelector` inside components; use `useRef`.
