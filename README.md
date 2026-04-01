# ☁️ Cloud Resume Challenge

![HTML](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Node.js](https://img.shields.io/badge/Node.js-22.x-339933?logo=nodedotjs&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=aws-lambda)
![Amazon API Gateway](https://img.shields.io/badge/AWS-API--Gateway-purple?logo=amazonaws)
![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blueviolet?logo=amazonaws)
![AWS CloudFront](https://img.shields.io/badge/AWS-CloudFront-orange?logo=amazonaws)
![AWS S3](https://img.shields.io/badge/AWS-S3-569A31?logo=amazonaws)
![AWS CloudFormation](https://img.shields.io/badge/AWS-CloudFormation-orange?logo=aws)
![AWS SAM](https://img.shields.io/badge/AWS-SAM-blue?logo=aws)
![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?logo=docker&logoColor=white)
![CI Tests](https://github.com/Aditya-Kumar-Verma/cloud-resume-challenge/actions/workflows/test.yml/badge.svg)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automation-2088FF?logo=githubactions)
![Visitors](https://visitor-badge.laobi.icu/badge?page_id=Aditya-Kumar-Verma.cloud-resume-challenge)

A fully serverless cloud resume built on AWS, deployed via a CI/CD pipeline, and served through a global CDN. This project implements the [Cloud Resume Challenge](https://cloudresumechallenge.dev/) — a hands-on project designed to demonstrate real-world cloud engineering skills.

**Live site:** [aditya-dev.tech](https://aditya-dev.tech)

---

## Architecture Overview

```
Browser → Route 53 → CloudFront (CDN) → S3 (static HTML/CSS/JS)
                                      ↓
                              JavaScript fetch()
                                      ↓
                         API Gateway (REST + HTTP)
                          ├── PUT /visitors  → PutVisitorFunction (Python)  → DynamoDB (visitorCountTable)
                          ├── GET /visitors  → GetVisitorFunction (Python)  → DynamoDB (visitorCountTable)
                          └── POST /track    → TrackVisitorFunction (Node.js) → DynamoDB (VisitorProfiles + VisitorEvents)
```

**Key design decisions:**
- S3 bucket is **private** — only CloudFront can read from it via Origin Access Control (OAC). Direct S3 URLs are blocked.
- All infrastructure is defined as code in `template.yaml` using AWS SAM (a CloudFormation extension).
- Every push to `main` automatically runs tests, deploys infrastructure, syncs the frontend, and invalidates the CloudFront cache.

---

## Project Structure

```
cloud-resume-challenge/
├── site/                          # Frontend (deployed to S3)
│   └── index.html                 # Resume page with visitor counter
│
├── get_visitor/                   # Lambda: reads visitor count from DynamoDB
│   ├── app.py
│   └── test_app.py
│
├── put_visitor/                   # Lambda: increments visitor count in DynamoDB
│   ├── app.py
│   ├── test_app.py
│   └── requirements.txt
│
├── src/
│   └── track-visitor/             # Lambda: records per-visitor geo + event data
│       ├── index.js
│       └── package.json
│
├── template.yaml                  # AWS SAM infrastructure definition
├── .github/workflows/test.yml     # CI/CD pipeline (GitHub Actions)
├── Makefile                       # Local development shortcuts
└── end-to-end-test/               # Puppeteer browser test
    └── index.js
```

---

## AWS Resources

All resources are defined in `template.yaml` and provisioned automatically by AWS SAM / CloudFormation.

| Resource | Type | Purpose |
|---|---|---|
| `MyCloudWebsite` | S3 Bucket | Hosts the static resume HTML |
| `MyOAC` | CloudFront OAC | Grants CloudFront-only access to S3 |
| `MyCloudWebsitePolicy` | S3 Bucket Policy | Enforces OAC — blocks all direct S3 access |
| `MyDistribution` | CloudFront Distribution | Global CDN, HTTPS, custom domain |
| `MyRoute53Record` | Route 53 Record Set | DNS for `aditya-dev.tech` and `www.aditya-dev.tech` |
| `VisitorTable` | DynamoDB Table | Stores total visitor count (`id=visitor`) |
| `VisitorProfilesTable` | DynamoDB Table | Stores per-visitor profile + geo data |
| `VisitorEventsTable` | DynamoDB Table | Logs each page visit event with timestamp |
| `PutVisitorFunction` | Lambda (Python 3.11) | Increments total visitor count atomically |
| `GetVisitorFunction` | Lambda (Python 3.11) | Reads and returns total visitor count |
| `TrackVisitorFunction` | Lambda (Node.js 22) | Hashes visitor IP+UA, logs geo data via ipapi.co |

---

## CI/CD Pipeline

Every push to `main` triggers a 4-stage pipeline defined in `.github/workflows/test.yml`:

```
push to main
     │
     ▼
┌─────────────────────────────┐
│  Job 1: test                │  Unit tests (Python) + live integration test
└─────────────┬───────────────┘
              │ must pass
              ▼
┌─────────────────────────────┐
│  Job 2: deploy-infra        │  sam build --use-container + sam deploy
└─────────────┬───────────────┘
              │ must pass
              ▼
┌─────────────────────────────┐
│  Job 3: deploy-site         │  aws s3 sync site/ → S3 bucket
└─────────────┬───────────────┘
              │ must pass
              ▼
┌─────────────────────────────┐
│  Job 4: invalidate-cache    │  CloudFront cache invalidation (/* paths)
└─────────────────────────────┘
```

AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CLOUDFRONT_DISTRIBUTION_ID`) are stored as GitHub Actions secrets and never committed to the repository.

---

## Lambda Functions

### `get_visitor` — Python 3.11
Reads the visitor count from DynamoDB using `get_item`. Returns `{ "count": N }` as JSON with CORS headers.

### `put_visitor` — Python 3.11
Atomically increments the visitor count using a conditional `SET` expression (`if_not_exists` + increment). Safe for concurrent requests — no read-modify-write race condition.

### `src/track-visitor` — Node.js 22 (ES Modules)
Extracts visitor IP and User-Agent, hashes them with SHA-256 (no PII stored), calls [ipapi.co](https://ipapi.co) to get geolocation, then writes a profile update and an event log to DynamoDB. Uses the native `fetch` API (Node 22 built-in) and `@aws-sdk/client-dynamodb`.

---

## Testing

### Unit tests
Each Lambda has a co-located unit test file using Python's `unittest` with `unittest.mock` to mock DynamoDB. No AWS credentials needed.

```bash
# Run get_visitor tests
cd get_visitor && python test_app.py

# Run put_visitor tests
cd put_visitor && python test_app.py
```

### Integration test
Hits the live API Gateway endpoint and asserts that a PUT followed by a GET increments the count. Requires the stack to be deployed.

```bash
echo '{ "DOMAIN_NAME": "api.aditya-dev.tech" }' > config.json
make integration-test
```

### End-to-end test
Uses Puppeteer to load the live site in a headless browser and assert that `#visitor-count` renders a non-empty value.

```bash
cd end-to-end-test
npm install
node index.js
```

---

## Local Development

### Prerequisites
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3.11](https://www.python.org/downloads/)
- [Node.js 22](https://nodejs.org/)
- [Docker](https://hub.docker.com/search/?type=edition&offering=community) (required for `sam build --use-container`)
- AWS credentials configured locally

### Build and deploy manually

```bash
# Build all Lambda functions in a Lambda-compatible Docker container
sam build --template-file template.yaml --use-container

# Deploy to AWS (first time — guided prompts)
sam deploy --guided

# Deploy to AWS (subsequent times)
sam deploy \
  --template-file template.yaml \
  --stack-name cloud-resume-challenge \
  --capabilities CAPABILITY_IAM \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --s3-bucket my-challenge-to-cloud23
```

### Useful Makefile commands

```bash
# Run the integration test against the live API
make integration-test

# Invoke PutVisitorFunction locally with a test event
make invoke-put

# Invoke GetVisitorFunction locally
make invoke-get
```

### View live Lambda logs

```bash
sam logs -n PutVisitorFunction --stack-name cloud-resume-challenge --tail
sam logs -n GetVisitorFunction --stack-name cloud-resume-challenge --tail
sam logs -n TrackVisitorFunction --stack-name cloud-resume-challenge --tail
```

---

## Security Notes

- The S3 bucket does **not** allow public access. All traffic is routed through CloudFront using Origin Access Control (OAC). Requests to the raw S3 URL return `403 Access Denied`.
- Visitor IPs are never stored in plaintext. `TrackVisitorFunction` hashes `IP + User-Agent` with SHA-256 before writing to DynamoDB.
- The CI/CD IAM user (`cloud-resume-cicd-automation-user`) follows least-privilege — it can only create/update roles prefixed with `cloud-resume-challenge-*`.
- All Lambda functions return `Access-Control-Allow-Origin: *` on both success and error responses for consistent CORS behaviour.

---

## Cleanup

To tear down all AWS resources created by this project:

```bash
sam delete --stack-name cloud-resume-challenge
```

> **Warning:** This deletes the S3 bucket, CloudFront distribution, DynamoDB tables, Lambda functions, and all associated IAM roles. The Route 53 records and ACM certificate are not deleted automatically.

---

## Resources

- [Cloud Resume Challenge](https://cloudresumechallenge.dev/) — the original challenge specification
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [AWS Serverless Application Repository](https://aws.amazon.com/serverless/serverlessrepo/)
