# C# / .NET — best practices

## Language and runtime

- Target the latest LTS version of .NET (currently .NET 8).
- Enable nullable reference types in every project: `<Nullable>enable</Nullable>`.
- Use `global using` directives for universally needed namespaces (e.g. `System`, `System.Collections.Generic`).

## Types and immutability

- Prefer `record` for value-semantic DTOs and `record struct` for small value types.
- Use `sealed` on classes that are not designed for inheritance.
- Mark properties `init`-only when they should not change after construction.
- Use `IReadOnlyList<T>` and `IReadOnlyDictionary<K,V>` for parameters and return types that must not be mutated.

## Null safety

- Return `null` only from methods explicitly annotated `T?`; use `Option`/result types for recoverable absence.
- Prefer pattern matching (`is null`, `is not null`) over `== null` comparisons.
- Never suppress nullable warnings with `!` unless the null check is provably impossible and a comment explains why.

## Error handling

- Use typed exceptions that derive from a project-specific base exception class.
- Do not use exceptions for control flow; return `bool`, `Result<T>`, or `OneOf<T, E>` for expected failures.
- Always include an `inner` exception when wrapping: `throw new DomainException("msg", ex)`.

## Async

- Mark every I/O-bound method `async Task<T>` and suffix the name with `Async`.
- Pass `CancellationToken` as the last parameter in every public async method.
- Never use `.Result` or `.Wait()` on a `Task` in synchronous code; it causes deadlocks.

## Naming conventions

| Entity | Convention | Example |
|---|---|---|
| Class / interface / enum | `PascalCase` | `UserRepository` |
| Method / property | `PascalCase` | `GetUserById` |
| Local variable / parameter | `camelCase` | `userId` |
| Private field | `_camelCase` | `_logger` |
| Constant | `PascalCase` | `MaxRetries` |
| Interface | Prefix `I` | `IUserRepository` |
| Async method | Suffix `Async` | `SaveAsync` |

## Anti-patterns

- Do not use `dynamic`; use generics or pattern matching instead.
- Do not catch `Exception` without re-throwing or logging.
- Do not use `Thread.Sleep`; use `await Task.Delay` in async contexts.
- Do not expose mutable collections through public properties.
