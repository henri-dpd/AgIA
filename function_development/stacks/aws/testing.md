# AWS — testing

## Strategy

| Layer | Tool |
|---|---|
| Unit (Lambda handler logic) | Vitest / Jest |
| Integration (AWS SDK calls) | LocalStack + Vitest |
| Infrastructure (CDK/Terraform) | CDK assertions / `terraform validate` |
| End-to-end | Postman / Newman, AWS Step Functions test execution |

## Unit testing a Lambda handler

```typescript
import { describe, it, expect } from "vitest";
import { handler } from "./handler.js";
import type { APIGatewayProxyEventV2 } from "aws-lambda";

const mockEvent = (body: object): APIGatewayProxyEventV2 =>
  ({ body: JSON.stringify(body) } as APIGatewayProxyEventV2);

describe("handler", () => {
  it("returns 200 for valid input", async () => {
    const result = await handler(mockEvent({ name: "Alice" }), {} as any);
    expect(result.statusCode).toBe(200);
  });

  it("returns 400 for missing name", async () => {
    const result = await handler(mockEvent({}), {} as any);
    expect(result.statusCode).toBe(400);
  });
});
```

## CDK stack assertions

```typescript
import { Template } from "aws-cdk-lib/assertions";
import { MyStack } from "../lib/my-stack";

it("creates a Lambda function with ARM64 architecture", () => {
  const template = Template.fromStack(new MyStack(app, "Test"));
  template.hasResourceProperties("AWS::Lambda::Function", {
    Architectures: ["arm64"],
  });
});
```

## LocalStack integration test

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Deploy stack to LocalStack
cdklocal deploy

# Invoke Lambda locally
awslocal lambda invoke --function-name MyFn /tmp/out.json
```
