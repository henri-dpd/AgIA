# React — workflow

## Step 1 — Understand the requirement

- Identify whether the task is a presentational component, a container, or a custom hook.
- List all props, state, and side effects.
- Note accessibility requirements and keyboard interactions.

## Step 2 — Design the component tree

- Sketch the parent-child relationship before coding.
- Decide where state should live (lowest common ancestor rule).
- Identify reusable pieces that already exist in the design system.

## Step 3 — Implement

- Create the component file and its co-located test file.
- Start with the render output; add interactivity and effects after the static render works.

## Step 4 — Lint and format

```bash
npx eslint --fix src/
npx prettier --write src/
```

## Step 5 — Test

```bash
npx vitest run
# or
npx jest
```

## Step 6 — Review checklist

- [ ] No class components.
- [ ] Every `useEffect` has an explicit dependency array.
- [ ] Props interface is fully typed with no `any`.
- [ ] Interactive elements are keyboard accessible.
- [ ] Storybook story added (if the project uses Storybook).
- [ ] Tests cover renders, interactions, and loading/error states.
