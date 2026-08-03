# Functional Requirements — ECS Fargate Demo

## Goal
Demonstrate a minimal, cost-effective Python service running on AWS ECS
Fargate, fronted by API Gateway, built as a Docker image and pushed to ECR,
with autoscaling (min 1 / max 2 tasks). Infrastructure defined in Terraform,
deployed via a GitHub Actions pipeline using AWS OIDC (no static credentials).

## Decisions

| Area | Decision |
|---|---|
| Region | `us-east-1` |
| App framework | FastAPI |
| Networking | Public subnets, tasks get public IPs directly (no NAT Gateway) |
| API Gateway | HTTP API + VPC Link to Fargate service |
| Task size | Smallest practical (0.25 vCPU / 0.5 GB) |
| Autoscaling | Target-tracking on CPU utilization, min 1 / max 2 tasks |
| Terraform state | Local state file (no remote backend) |
| CI/CD | GitHub Actions, authenticated via AWS OIDC (no stored AWS keys) |
| Environments | Single environment only |

## In scope
- **App**: FastAPI service with a `/health` endpoint and one demo endpoint
  (e.g. `/hello`).
- **Container**: Dockerfile, image pushed to a private ECR repository.
- **Compute**: ECS Fargate service, 0.25 vCPU / 0.5 GB tasks, min 1 / max 2,
  scaling via target-tracking on CPU utilization.
- **Networking**: New VPC with public subnets; Fargate tasks run with public
  IPs (no NAT Gateway, keeps monthly cost near zero when idle).
- **API Gateway**: HTTP API using a VPC Link to privately reach the Fargate
  service.
- **IaC**: VPC, ECS cluster/service/task definition, ECR repo, API Gateway +
  VPC Link, IAM roles, autoscaling policies — all in Terraform, local state.
- **CI/CD**: GitHub Actions workflow that:
  1. Authenticates to AWS via OIDC (assumes an IAM role, no long-lived keys).
  2. Runs `terraform plan`/`apply` for infra changes.
  3. Builds the Docker image and pushes it to ECR.
  4. Forces a new ECS deployment so the service picks up the new image.

## Out of scope
- Custom domain / TLS certificate for the API.
- Authentication/authorization on the API itself.
- Multi-environment (dev/staging/prod) setup.
- Centralized logging/monitoring dashboards beyond default CloudWatch logs.
- Database or persistent storage.
- Remote Terraform state backend (S3/DynamoDB).

## Cost notes
- No NAT Gateway, no ALB, no remote state resources — the only ~always-on
  cost is 1 Fargate task (0.25 vCPU/0.5GB) plus negligible ECR storage and
  per-request API Gateway/CloudWatch charges.
