# NestJS — best practices

## Architecture

- Follow the **module → controller → service → repository** layering; never skip layers.
- Each domain feature lives in its own module: `users/users.module.ts` exports `UsersService` and declares `UsersController`.
- Use `forwardRef()` sparingly; circular module dependencies usually indicate a design flaw.

## Dependency injection

- Register every service as `@Injectable()` and import it through the module system, not direct instantiation.
- Use **custom providers** (`useFactory`, `useValue`) for integrations that require async initialisation (database connections, config).
- Scope services as `REQUEST` only when they genuinely need per-request isolation; default to `DEFAULT` (singleton) scope.

## Controllers

- Controllers handle HTTP concerns only: routing, request parsing, and response shaping.
- Use **DTOs** with `class-validator` decorators for all incoming payloads; never pass raw `Request` objects to services.
- Use **`@ApiProperty()`** decorators (Swagger) on every DTO field in API-facing modules.

## Validation and transformation

- Enable the global `ValidationPipe` with `whitelist: true` and `forbidNonWhitelisted: true`.
- Use `@Transform` from `class-transformer` to normalise inputs (trim strings, parse dates) before validation.
- Never trust client-provided IDs for authorisation; verify ownership in the service layer.

## Error handling

- Throw NestJS `HttpException` subclasses in controllers for HTTP-specific errors.
- Throw domain exceptions in services; let an exception filter translate them to HTTP responses.
- Use a global `ExceptionFilter` to log unexpected errors and return consistent error shapes.

## Security

- Use the `@nestjs/throttler` package to rate-limit public endpoints.
- Use `helmet()` middleware for HTTP security headers.
- Use `@nestjs/passport` with JWT strategy for authentication; validate the token in a Guard.
- Never expose internal stack traces or database errors to API consumers.

## Naming conventions

| Entity | Convention |
|---|---|
| Module | `PascalCase` + `Module` — `UsersModule` |
| Controller | `PascalCase` + `Controller` — `UsersController` |
| Service | `PascalCase` + `Service` — `UsersService` |
| DTO | `PascalCase` + `Dto` — `CreateUserDto` |
| Guard | `PascalCase` + `Guard` — `JwtAuthGuard` |
| File | `kebab-case.type.ts` |

## Anti-patterns

- Do not perform database queries directly in controllers.
- Do not share mutable state across singleton services without synchronisation.
- Do not disable the `ValidationPipe`; all inputs must be validated.
- Do not return raw Prisma/TypeORM entities to clients; map to response DTOs.
