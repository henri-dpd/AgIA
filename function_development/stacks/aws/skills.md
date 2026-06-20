# AWS — skills

## Core services by category

### Compute

| Service | Use case |
|---|---|
| Lambda | Event-driven functions, API backends |
| ECS Fargate | Containerised long-running services |
| EKS | Kubernetes workloads |
| EC2 | When full VM control is required |

### Storage

| Service | Use case |
|---|---|
| S3 | Object storage, static assets, backups |
| EBS | Block storage for EC2 |
| EFS | Shared file system for ECS/EC2 |
| DynamoDB | NoSQL key-value and document store |
| RDS / Aurora | Relational databases |
| ElastiCache | Redis/Memcached caching |

### Networking

| Service | Use case |
|---|---|
| VPC | Isolated network |
| ALB / NLB | Load balancing |
| CloudFront | CDN and edge caching |
| Route 53 | DNS and health checks |
| API Gateway | HTTP and WebSocket APIs |

### Developer tools

| Tool | Purpose |
|---|---|
| AWS CDK | Infrastructure as code (TypeScript/Python) |
| Terraform | Multi-cloud infrastructure as code |
| AWS SAM | Serverless application model |
| AWS CLI | Command-line access |
| LocalStack | Local AWS emulation for testing |

## CDK Lambda function example

```typescript
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";

const fn = new lambda.Function(stack, "MyFn", {
  runtime: lambda.Runtime.NODEJS_20_X,
  architecture: lambda.Architecture.ARM_64,
  handler: "index.handler",
  code: lambda.Code.fromAsset("dist"),
  timeout: cdk.Duration.seconds(30),
  memorySize: 256,
  environment: { LOG_LEVEL: "info" },
});
```
