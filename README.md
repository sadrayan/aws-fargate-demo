# aws-fargate-demo

A minimal, cost-conscious demo of a Python service running on **ECS Fargate**,
fronted by **API Gateway** (HTTP API + VPC Link), built as a Docker image and
pushed to **ECR**, with CPU-based autoscaling (1-2 tasks). Infra is Terraform,
deployed by GitHub Actions via AWS OIDC (no static AWS keys).

See [REQUIREMENTS.md](REQUIREMENTS.md) for the full design decisions and
scope.

## Architecture

```
GitHub push to main
  -> GitHub Actions (OIDC-assumed role)
      -> terraform init
      -> docker build & push -> ECR
      -> terraform apply (new image_tag)
      -> smoke test GET /health

Client -> API Gateway (HTTP API) -> VPC Link -> Cloud Map -> ECS Fargate task(s)
                                                                (0.25 vCPU/0.5GB, min 1 / max 2,
                                                                 target-tracking on CPU 70%)
```

- Public subnets only, tasks get public IPs directly — no NAT Gateway, so
  idle cost stays near zero.
- Terraform state is remote (S3 backend with native S3 locking), not local.
- A CloudWatch dashboard (`terraform/dashboard.tf`) covers ECS CPU/Memory,
  API Gateway requests/errors/latency, and autoscaling alarms — built from
  free default metrics only.

## App endpoints

- `GET /health` — `{"status": "ok"}`
- `GET /hello` — demo payload
- `GET /burn?seconds=2.0` — pegs one CPU core for `seconds` (clamped 0.1-10);
  used to trigger autoscaling in load tests

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker (to build the image)
- Terraform >= 1.10
- AWS credentials with access to the target account (for local `terraform`
  runs); CI uses OIDC instead

## Bootstrap (local dev)

```bash
uv sync                 # installs deps incl. dev group into .venv
uv run pytest           # run tests
uv run uvicorn app.main:app --reload   # run the API locally at :8000
```

## Deploying

Deployment is automatic on push to `main` via
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml): it assumes
an AWS role via OIDC, runs `terraform apply`, builds/pushes the Docker
image to ECR, and smoke-tests `/health`.

To run the same steps manually:

```bash
cd terraform
terraform init
terraform apply -var="image_tag=<tag>"

docker build -t <ecr-repo-url>:<tag> .
docker push <ecr-repo-url>:<tag>

terraform output api_invoke_url   # base URL for the deployed API
```

Required GitHub environment secret: `AWS_ROLE_ARN` (the deploy role's ARN;
see `terraform/main.tf` for the role and its trust policy).

## Load testing autoscaling

`scripts/load_test_autoscaling.py` hammers `/burn` with concurrent workers
and polls the ECS service's task count via boto3 until it scales up (or
times out), logging samples to a JSON-lines file.

```bash
uv run python scripts/load_test_autoscaling.py --url "$(cd terraform && terraform output -raw api_invoke_url)"
```

Useful flags: `--target-count`, `--workers`, `--burn-seconds`,
`--poll-interval`, `--timeout`, `--output`.

## Project layout

```
app/                      FastAPI app + tests
scripts/                  load_test_autoscaling.py
terraform/                VPC, ECS, ECR, API Gateway, IAM, CloudWatch dashboard
.github/workflows/        CI/CD pipeline (deploy.yml)
Dockerfile                uv-based build, runs uvicorn
REQUIREMENTS.md           design decisions, scope, cost notes
```
