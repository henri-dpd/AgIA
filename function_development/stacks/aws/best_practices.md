# AWS — best practices

## Infrastructure as code

- Define all AWS resources with **AWS CDK** (TypeScript) or **Terraform**; never create resources manually in the console for production environments.
- Use **named constructs** and consistent stack naming: `AppStack-{env}-{region}`.
- Store Terraform state in an S3 backend with DynamoDB locking; never use local state in shared environments.
- Tag every resource with at minimum: `Project`, `Environment`, `Owner`, `CostCenter`.

## Security

- Apply the **principle of least privilege** to every IAM role and policy; never use `*` as the `Action` or `Resource` unless absolutely necessary and documented.
- Rotate IAM access keys regularly; prefer **IAM roles** for EC2/Lambda over long-lived keys.
- Enable **CloudTrail** in all regions and retain logs for at least one year.
- Enable **AWS Config** to detect configuration drift.
- Enable **GuardDuty** and **Security Hub** in every account.
- Store secrets in **AWS Secrets Manager** or **SSM Parameter Store (SecureString)**; never hard-code credentials.

## Compute

- Prefer **Lambda** for event-driven and short-lived workloads; use ECS Fargate for long-running services.
- Set Lambda memory, timeout, and concurrency limits explicitly; never rely on defaults for production.
- Use **Lambda Layers** for shared dependencies; keep deployment packages small.
- Use **Graviton (ARM64)** instances for Lambda and ECS for better price/performance.

## Storage

- Enforce **S3 Block Public Access** at the account level; use bucket policies to grant specific access.
- Enable **S3 Versioning** and **Object Lock** for compliance buckets.
- Enable **encryption at rest** (SSE-S3 or SSE-KMS) for all S3 buckets, RDS instances, and DynamoDB tables.
- Set lifecycle policies on S3 to move old objects to Glacier.

## Networking

- Deploy workloads in a **VPC**; never expose databases to the public internet.
- Use **private subnets** for compute and data; use **public subnets** only for load balancers and NAT gateways.
- Use **VPC endpoints** for S3 and DynamoDB to avoid NAT gateway charges and keep traffic private.
- Apply **Security Groups** with minimal required rules; deny all ingress by default.

## Observability

- Emit structured logs to **CloudWatch Logs** with a consistent schema (JSON with `level`, `requestId`, `service`).
- Create **CloudWatch Alarms** for P99 latency, error rate, and queue depth.
- Use **X-Ray** or **AWS Distro for OpenTelemetry** for distributed tracing.
- Define **CloudWatch Dashboards** per service.

## Cost management

- Use **Cost Explorer** and **AWS Budgets** to track spend per environment and team.
- Enable **Compute Optimizer** recommendations.
- Use **Savings Plans** or **Reserved Instances** for steady-state workloads.
- Delete unused resources; use AWS Config rules to detect idle resources.

## Anti-patterns

- Do not use the AWS root account for day-to-day operations; use IAM users or SSO roles.
- Do not store secrets in Lambda environment variables in plain text; use Secrets Manager.
- Do not deploy directly from a developer laptop; use a CI/CD pipeline with OIDC authentication.
- Do not create security groups that allow `0.0.0.0/0` inbound on any port other than 80/443.
