# NestJS — testing

## Framework

NestJS ships with `@nestjs/testing`; use it with **Jest** (default) or **Vitest**.

## Unit test — service

```typescript
describe("UsersService", () => {
  let service: UsersService;
  const mockRepo = { save: jest.fn(), findById: jest.fn() };

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        UsersService,
        { provide: UsersRepository, useValue: mockRepo },
      ],
    }).compile();
    service = module.get(UsersService);
  });

  it("creates a user", async () => {
    const dto = { name: "Alice", email: "alice@example.com" };
    mockRepo.save.mockResolvedValue({ id: "1", ...dto });
    const result = await service.create(dto);
    expect(result.id).toBe("1");
  });
});
```

## Integration test — controller

```typescript
describe("UsersController (integration)", () => {
  let app: INestApplication;

  beforeAll(async () => {
    const module = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(UsersRepository)
      .useValue({ save: jest.fn().mockResolvedValue({ id: "1", name: "Alice" }) })
      .compile();
    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
    await app.init();
  });
  afterAll(() => app.close());

  it("POST /users returns 201", () => {
    return request(app.getHttpServer())
      .post("/users")
      .send({ name: "Alice", email: "alice@example.com" })
      .expect(201);
  });
});
```

## End-to-end

```bash
npm run test:e2e
```
