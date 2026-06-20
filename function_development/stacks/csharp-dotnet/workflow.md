# C# / .NET — workflow

## Step 1 — Understand the requirement

- Identify the domain objects and map them to C# types (`record`, `class`, `struct`).
- Decide the error-handling strategy: exceptions, result types, or nullable returns.
- Note async requirements; every I/O operation must be async.

## Step 2 — Set up the project

```bash
dotnet new classlib -n MyLib --framework net8.0
dotnet new xunit -n MyLib.Tests
dotnet add MyLib.Tests reference MyLib
```

## Step 3 — Implement

- Enable `<Nullable>enable</Nullable>` and `<ImplicitUsings>enable</ImplicitUsings>` in `.csproj`.
- Use primary constructors (C# 12) for simple dependency injection.
- Run `dotnet build` before committing.

## Step 4 — Lint and format

```bash
dotnet format
dotnet build /warnaserror
```

## Step 5 — Test

```bash
dotnet test --no-build --logger "console;verbosity=normal"
```

## Step 6 — Review checklist

- [ ] Nullable reference types enabled; no `!` suppressions without comment.
- [ ] All async methods suffixed `Async` and accept `CancellationToken`.
- [ ] No `.Result` or `.Wait()` on `Task`.
- [ ] All public APIs documented with XML doc comments.
- [ ] Tests cover happy path, null inputs, and exception paths.
