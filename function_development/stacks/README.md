# Technology stacks

Each subfolder contains stack-specific guidelines that the Planner agent loads at runtime when a `--stack` value is provided. The Planner injects these guidelines into its analysis and passes the enriched plan to the Coder and Auditor agents.

## Available stacks

| Folder | Technologies |
|---|---|
| `typescript/` | TypeScript |
| `javascript/` | JavaScript (ES modules, CommonJS) |
| `csharp-dotnet/` | C# / .NET |
| `react/` | React (component and hook development) |
| `nextjs/` | Next.js (App Router and Pages Router) |
| `angular/` | Angular |
| `nodejs/` | Node.js (server-side JavaScript/TypeScript) |
| `nestjs/` | NestJS (Node.js framework) |
| `aws/` | AWS cloud services and infrastructure |
| `python/` | Python (standard library and ecosystem) |

## Files per stack

| File | Content |
|---|---|
| `best_practices.md` | Coding standards, anti-patterns, naming conventions |
| `workflow.md` | Step-by-step development and review flow |
| `skills.md` | Tooling, libraries, and configuration patterns |
| `testing.md` | Testing frameworks, strategies, and examples |

## How stacks compose

A project may use multiple stacks. Pass the most specific primary stack to `--stack` (for example `nestjs` rather than `nodejs` for a NestJS service). The Planner agent is responsible for combining guidelines from related stacks when the plan references multiple technologies.

## Adding a new stack

1. Create a new folder under `function_development/stacks/`.
2. Add `best_practices.md`, `workflow.md`, `skills.md`, and `testing.md`.
3. Register the stack name in this README table.
