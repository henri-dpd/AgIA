# C# / .NET — testing

## Framework

Use **xUnit** for new .NET projects; it is the default for `dotnet new xunit`.

## Test class conventions

```csharp
public sealed class UserServiceTests
{
    private readonly IUserRepository _repository = Substitute.For<IUserRepository>();
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _sut = new UserService(_repository, NullLogger<UserService>.Instance);
    }

    [Fact]
    public async Task GetByIdAsync_ReturnsUser_WhenFound()
    {
        // Arrange
        var id = Guid.NewGuid();
        var expected = new User(id, "Alice");
        _repository.FindAsync(id, default).Returns(expected);

        // Act
        var result = await _sut.GetByIdAsync(id, default);

        // Assert
        result.Should().BeEquivalentTo(expected);
    }

    [Fact]
    public async Task GetByIdAsync_ReturnsNull_WhenNotFound()
    {
        _repository.FindAsync(Arg.Any<Guid>(), default).Returns((User?)null);
        var result = await _sut.GetByIdAsync(Guid.NewGuid(), default);
        result.Should().BeNull();
    }
}
```

## Parameterised tests

```csharp
[Theory]
[InlineData(0, 50, 100, 0.5)]
[InlineData(0, 0, 100, 0.0)]
public void Normalize_ReturnsExpected(double min, double value, double max, double expected)
{
    Normalize(min, value, max).Should().BeApproximately(expected, 1e-9);
}
```

## Mocking

- Use **NSubstitute** (`Substitute.For<T>()`) for interface mocks.
- Avoid mocking concrete classes; refactor to depend on interfaces instead.

## Running tests

```bash
dotnet test --collect:"XPlat Code Coverage"
reportgenerator -reports:coverage.xml -targetdir:coverage-report
```
