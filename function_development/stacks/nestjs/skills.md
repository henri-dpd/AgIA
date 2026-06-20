# NestJS — skills

## Core packages

| Package | Purpose |
|---|---|
| `@nestjs/core` + `@nestjs/common` | Framework core |
| `@nestjs/platform-fastify` | Fastify adapter (preferred over Express for performance) |
| `@nestjs/config` | Environment configuration |
| `@nestjs/swagger` | OpenAPI documentation |
| `@nestjs/throttler` | Rate limiting |
| `@nestjs/passport` + `passport-jwt` | JWT authentication |
| `class-validator` + `class-transformer` | DTO validation and transformation |
| `@prisma/client` | Database ORM |

## Bootstrap pattern

```typescript
// main.ts
import { NestFactory } from "@nestjs/core";
import { NestFastifyApplication, FastifyAdapter } from "@nestjs/platform-fastify";
import { ValidationPipe } from "@nestjs/common";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import { AppModule } from "./app.module";
import { AllExceptionsFilter } from "./filters/all-exceptions.filter";

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(AppModule, new FastifyAdapter());
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }));
  app.useGlobalFilters(new AllExceptionsFilter());

  const document = SwaggerModule.createDocument(
    app,
    new DocumentBuilder()
      .setTitle("API")
      .setVersion("1.0")
      .addBearerAuth()
      .build(),
  );
  SwaggerModule.setup("docs", app, document);

  await app.listen(process.env.PORT ?? 3000, "0.0.0.0");
}
bootstrap();
```

## Exception filter skeleton

```typescript
import { ArgumentsHost, Catch, ExceptionFilter, HttpException } from "@nestjs/common";

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const status = exception instanceof HttpException ? exception.getStatus() : 500;
    ctx.getResponse().status(status).send({ statusCode: status, message: "Internal server error" });
  }
}
```
