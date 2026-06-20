# NestJS — workflow

## Step 1 — Scaffold the module

```bash
nest generate module users
nest generate controller users
nest generate service users
```

## Step 2 — Define the DTO

```typescript
// users/dto/create-user.dto.ts
import { IsEmail, IsString, MinLength } from "class-validator";

export class CreateUserDto {
  @IsString() @MinLength(1)
  name: string;

  @IsEmail()
  email: string;
}
```

## Step 3 — Implement the service

```typescript
@Injectable()
export class UsersService {
  constructor(private readonly usersRepository: UsersRepository) {}

  async create(dto: CreateUserDto): Promise<User> {
    return this.usersRepository.save(dto);
  }
}
```

## Step 4 — Implement the controller

```typescript
@Controller("users")
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(@Body() dto: CreateUserDto) {
    return this.usersService.create(dto);
  }
}
```

## Step 5 — Lint and test

```bash
npm run lint
npm run test
npm run test:e2e
```

## Step 6 — Review checklist

- [ ] Global `ValidationPipe` with `whitelist` and `forbidNonWhitelisted` enabled.
- [ ] Controllers contain no business logic.
- [ ] DTOs validated with `class-validator`.
- [ ] Services do not return raw ORM entities to controllers.
- [ ] Auth protected by a Guard; not inline in the route handler.
