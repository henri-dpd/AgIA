# C# / .NET — skills

## Core tooling

| Tool | Purpose |
|---|---|
| `dotnet CLI` | Build, test, publish, scaffold |
| Roslyn analyzers | Static analysis at compile time |
| `dotnet format` | Code formatting (EditorConfig) |
| xUnit / NUnit / MSTest | Unit testing |
| Moq / NSubstitute | Mocking |
| Serilog / Microsoft.Extensions.Logging | Structured logging |

## NuGet packages (frequently used)

| Package | Purpose |
|---|---|
| `Microsoft.Extensions.DependencyInjection` | DI container |
| `Microsoft.Extensions.Options` | Typed configuration |
| `FluentValidation` | Input validation |
| `Polly` | Resilience policies (retry, circuit breaker) |
| `FluentAssertions` | Expressive test assertions |
| `BenchmarkDotNet` | Micro-benchmarking |

## Dependency injection pattern

```csharp
public sealed class UserService(IUserRepository repository, ILogger<UserService> logger)
{
    public async Task<User?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        logger.LogDebug("Fetching user {UserId}", id);
        return await repository.FindAsync(id, ct);
    }
}
```

## Result type pattern

```csharp
public readonly record struct Result<T>(T? Value, string? Error)
{
    public bool IsSuccess => Error is null;
    public static Result<T> Ok(T value) => new(value, null);
    public static Result<T> Fail(string error) => new(default, error);
}
```
