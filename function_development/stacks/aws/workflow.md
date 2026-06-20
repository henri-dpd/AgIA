# AWS — workflow

## Step 1 — Design the architecture

- Draw a diagram with all services, data flows, and trust boundaries.
- Identify which services handle PII or regulated data; note compliance requirements.
- Estimate cost with the AWS Pricing Calculator before provisioning.

## Step 2 — Set up accounts and access

```bash
# Authenticate via SSO
aws sso login --profile dev
export AWS_PROFILE=dev
```

- Use separate AWS accounts per environment (`dev`, `staging`, `prod`).
- Grant access through AWS IAM Identity Center (SSO); avoid long-lived IAM user keys.

## Step 3 — Write infrastructure as code

```bash
# CDK (TypeScript)
cdk init app --language typescript
cdk deploy --profile dev

# Terraform
terraform init
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

## Step 4 — CI/CD pipeline

- Use GitHub Actions with OIDC to assume a deployment role; no stored AWS credentials.
- Run `cdk diff` or `terraform plan` in PR checks; apply only from the main branch.

## Step 5 — Deploy and verify

```bash
# Verify Lambda deployment
aws lambda invoke --function-name my-function /tmp/out.json && cat /tmp/out.json

# Check CloudWatch logs
aws logs tail /aws/lambda/my-function --follow
```

## Step 6 — Review checklist

- [ ] All resources tagged with `Project`, `Environment`, `Owner`.
- [ ] IAM roles follow least-privilege; no wildcard `*` actions without justification.
- [ ] Secrets stored in Secrets Manager; not in environment variables or code.
- [ ] CloudWatch alarms defined for error rate and latency.
- [ ] CloudTrail enabled in all regions.
- [ ] Deployment uses OIDC; no long-lived access keys in CI.
