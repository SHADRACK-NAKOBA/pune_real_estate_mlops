# Production Readiness Guide — Pune Real Estate Price Prediction API
**Author: Shadrack Nakoba | Version: 1.0 | Date: June 2026**

> This guide is written for a junior developer who needs to take this project from a working local state to a fully hardened, monitored, live cloud deployment — without needing to ask questions.

---

## Table of Contents
1. [Production Checklist](#1-production-checklist)
2. [Environment Variables](#2-environment-variables)
3. [Docker Production Setup](#3-docker-production-setup)
4. [AWS EC2 Production Deployment](#4-aws-ec2-production-deployment)
5. [AWS ECS Fargate Setup](#5-aws-ecs-fargate-setup)
6. [Kubernetes Production Setup](#6-kubernetes-production-setup)
7. [GitHub Actions Full CI/CD](#7-github-actions-full-cicd)
8. [Monitoring Setup](#8-monitoring-setup)
9. [Security Hardening](#9-security-hardening)
10. [Scaling Strategy](#10-scaling-strategy)
11. [Disaster Recovery](#11-disaster-recovery)
12. [Cost Estimation](#12-cost-estimation)
13. [Maintenance Guide](#13-maintenance-guide)

---

## 1. Production Checklist

Work through this list top-to-bottom before declaring the system live. Check each item only when fully verified.

### Code Quality
- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] No hardcoded secrets, passwords, or AWS keys in any source file
- [ ] `.env` is in `.gitignore` and never committed
- [ ] `requirements.txt` has been updated with all current dependencies
- [ ] `models/best_model.pkl` loads without errors in Python 3.10

### Docker
- [ ] `docker build` completes without errors from a clean state
- [ ] `docker run` starts the container and `/health` returns `{"status": "ok"}`
- [ ] Container starts within 30 seconds (HEALTHCHECK passes)
- [ ] Docker image size is reasonable (target: under 2GB with all dependencies)
- [ ] Image has been tagged and pushed to Docker Hub or AWS ECR
- [ ] No sensitive data baked into the Docker image (no `.env`, no private keys)

### API
- [ ] `GET /health` returns `{"status": "ok", "model_loaded": true}`
- [ ] `POST /predict` returns a valid price for a sample request
- [ ] `POST /predict` returns a `422` error for invalid input (negative area_sqft)
- [ ] `POST /predict/batch` works for 2, 10, and 100 items
- [ ] Swagger UI at `/docs` loads and all endpoints are documented
- [ ] HTTPS is configured (not HTTP-only) before going live

### Infrastructure
- [ ] Security groups restrict inbound traffic to ports 80, 443 only (not 8000 directly)
- [ ] SSH access to EC2 is limited to your IP address (not 0.0.0.0/0)
- [ ] IAM roles follow least-privilege principle
- [ ] CloudWatch logs are flowing (you can see API startup logs in AWS console)
- [ ] CloudWatch alarm is set for 5xx errors
- [ ] Backup of `models/best_model.pkl` uploaded to S3

### DNS and SSL
- [ ] Domain name points to EC2 Elastic IP or Load Balancer DNS
- [ ] SSL certificate is issued (Let's Encrypt or ACM)
- [ ] HTTPS redirect from HTTP is configured in Nginx
- [ ] Certificate renewal is automated (certbot timer or ACM auto-renewal)

### CI/CD
- [ ] All GitHub Actions secrets are set (see Section 2)
- [ ] A test push to `main` branch triggers the full CI/CD pipeline
- [ ] Pipeline: lint → test → docker build → docker push → deploy (all green)
- [ ] Deployment does not cause downtime (rolling update or blue/green)

### Final Sign-Off
- [ ] API accessible at public HTTPS URL
- [ ] A complete end-to-end test: POST to `/predict` via curl from a different machine
- [ ] Monitor CloudWatch for 15 minutes after deployment — no error spikes

---

## 2. Environment Variables

### Local Development (`.env` file — never commit this)
```env
# API Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
MODEL_PATH=models/best_model.pkl

# MLflow
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
MLFLOW_EXPERIMENT_NAME=pune_real_estate_price_prediction

# Security (for production use a real random string)
API_KEY=dev-local-key-change-in-prod

# AWS (for local testing of cloud interactions only)
AWS_REGION=ap-south-1
```

### GitHub Actions Secrets (required for CI/CD)
Go to: GitHub → Your Repo → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value | Where Used |
|---|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username | Build and push step |
| `DOCKER_PASSWORD` | Docker Hub access token (not password) | Build and push step |
| `AWS_ACCESS_KEY_ID` | IAM user access key | AWS CLI in GitHub Actions |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | AWS CLI in GitHub Actions |
| `EC2_HOST` | EC2 public IP or domain | SSH deploy step |
| `EC2_SSH_KEY` | Contents of your `.pem` file | SSH deploy step |
| `EC2_USER` | `ubuntu` (for Ubuntu AMI) | SSH deploy step |

**How to create a Docker Hub access token (not password):**
1. Go to hub.docker.com → Account Settings → Security → New Access Token
2. Name it `github-actions`, permission: Read/Write
3. Copy the token — it shows only once
4. Add as `DOCKER_PASSWORD` secret in GitHub

**How to create an IAM user for GitHub Actions:**
1. AWS Console → IAM → Users → Create user → `github-actions-deploy`
2. Attach policies: `AmazonEC2FullAccess`, `AmazonECS_FullAccess`, `AmazonEC2ContainerRegistryFullAccess`
3. Create access key → Application running outside AWS
4. Copy Access Key ID and Secret Access Key → Add to GitHub secrets

### Production Server (`/etc/environment` on EC2 or ECS task definition env vars)
```env
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
MODEL_PATH=/app/models/best_model.pkl
MLFLOW_TRACKING_URI=sqlite:////app/mlflow.db
API_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
AWS_REGION=ap-south-1
LOG_LEVEL=info
```

---

## 3. Docker Production Setup

### Production Dockerfile
The existing Dockerfile is already production-ready, but this enhanced version adds a non-root user for security:

```dockerfile
# deployment/docker/Dockerfile.prod
FROM python:3.10-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install Python dependencies (layer cache: copy requirements first)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY models/ ./models/

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command: 2 workers for concurrency
CMD ["uvicorn", "src.api.fastapi_app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log"]
```

### Production Docker Compose
```yaml
# deployment/docker/docker-compose.prod.yml
version: "3.9"

services:
  api:
    image: YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
    container_name: pune_re_api
    ports:
      - "8000:8000"
    volumes:
      - /home/ubuntu/pune_real_estate/models:/app/models:ro
    environment:
      - APP_ENV=production
      - MODEL_PATH=/app/models/best_model.pkl
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Building and Running Locally (Windows PowerShell)
```powershell
# Build the image
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .

# Run locally
docker run -d `
  --name pune_api_test `
  -p 8000:8000 `
  -v "${PWD}/models:/app/models:ro" `
  pune-real-estate-api:latest

# Test it
curl http://localhost:8000/health

# See logs
docker logs pune_api_test -f

# Stop and remove
docker stop pune_api_test
docker rm pune_api_test
```

### Tagging and Pushing to Docker Hub
```powershell
# Login
docker login -u YOUR_DOCKERHUB_USERNAME

# Tag with your username
docker tag pune-real-estate-api:latest YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker tag pune-real-estate-api:latest YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.0.0

# Push both tags
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.0.0
```

---

## 4. AWS EC2 Production Deployment

### Step 4.1 — Launch EC2 Instance
1. Open AWS Console → EC2 → Launch Instance
2. Settings:
   - Name: `pune-real-estate-api`
   - AMI: Ubuntu Server 22.04 LTS (64-bit x86)
   - Instance type: `t3.small` (2 vCPU, 2GB RAM) — sufficient for this API
   - Key pair: Create new → `pune-api-key` → Download `.pem` file → keep safe
   - Network settings:
     - VPC: Default VPC
     - Auto-assign public IP: Enable
   - Firewall (Security group): Create new security group
     - Add rule: SSH — Port 22 — Source: My IP (NOT 0.0.0.0/0)
     - Add rule: HTTP — Port 80 — Source: Anywhere (0.0.0.0/0)
     - Add rule: HTTPS — Port 443 — Source: Anywhere (0.0.0.0/0)
     - **Do NOT add Port 8000 — Nginx will proxy from 80 to 8000 internally**
   - Storage: 20GB gp3

3. Launch → Note the Public IPv4 address

### Step 4.2 — Associate Elastic IP (prevents IP changing on reboot)
1. EC2 Console → Elastic IPs → Allocate Elastic IP address
2. Select the new Elastic IP → Actions → Associate Elastic IP
3. Choose your instance → Associate
4. The Elastic IP is now permanently attached to your EC2 instance

### Step 4.3 — SSH into EC2 (from Windows PowerShell)
```powershell
# Fix key permissions (Windows PowerShell)
$keyPath = "C:\Users\admin\Downloads\pune-api-key.pem"
icacls $keyPath /inheritance:r
icacls $keyPath /grant:r "${env:USERNAME}:R"

# Connect (replace YOUR_EC2_IP with Elastic IP)
ssh -i $keyPath ubuntu@YOUR_EC2_IP
```

### Step 4.4 — Server Setup (run inside EC2 SSH session)
```bash
# System update
sudo apt-get update -y && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx and Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Log out and back in (to apply docker group membership)
exit
```

SSH back in, then continue:

```bash
# Verify Docker works without sudo
docker ps

# Pull your image from Docker Hub
docker pull YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest

# Create app directory
mkdir -p ~/pune_app/models

# Upload your model file (run this from your Windows machine, not the EC2 session)
# scp -i C:\Users\admin\Downloads\pune-api-key.pem models/best_model.pkl ubuntu@YOUR_EC2_IP:~/pune_app/models/

# Run the container
docker run -d \
  --name pune_api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v ~/pune_app/models:/app/models:ro \
  -e APP_ENV=production \
  YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:latest

# Verify it's running
docker ps
curl http://localhost:8000/health
```

### Step 4.5 — Configure Nginx as Reverse Proxy
```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/pune_api > /dev/null <<'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/pune_api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test config and restart
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Test via Nginx (port 80, not 8000)
curl http://YOUR_EC2_IP/health
```

### Step 4.6 — SSL Certificate with Let's Encrypt

**Prerequisite:** You must have a domain name pointing to your EC2 Elastic IP. Go to your domain registrar (GoDaddy, Namecheap, Route 53) and add an A record:
- Type: A
- Name: `@` or `api` (depending on whether you want root domain or subdomain)
- Value: YOUR_EC2_ELASTIC_IP
- TTL: 300

Wait 5-10 minutes for DNS propagation, then:

```bash
# Replace with your actual domain
DOMAIN="api.yourdomain.com"

# Get certificate (interactive — enter email and agree to ToS)
sudo certbot --nginx -d $DOMAIN

# Certbot auto-edits Nginx config to add SSL
# After completion, test HTTPS:
curl https://$DOMAIN/health

# Certbot auto-renewal is already set up (check with):
sudo systemctl status certbot.timer

# Manual renewal test (dry run — does not actually renew):
sudo certbot renew --dry-run
```

After certbot runs, your Nginx config automatically becomes:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;  # HTTP → HTTPS redirect
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ... headers ...
    }
}
```

### Step 4.7 — Verify Deployment
```bash
# From your Windows machine, test the live API:
curl https://api.yourdomain.com/health
# Expected: {"status":"ok","model_loaded":true}

curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -d '{"area_sqft":1000,"amenity_score":4,"has_clubhouse":1,"has_school":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'
# Expected: {"predicted_price_lakhs":87.4,...}
```

---

## 5. AWS ECS Fargate Setup

ECS Fargate runs your Docker container without managing any EC2 instances. AWS handles the underlying servers.

### Step 5.1 — Push Image to Amazon ECR (Elastic Container Registry)
```powershell
# Install AWS CLI (Windows)
winget install Amazon.AWSCLI

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output format (json)

# Create ECR repository
aws ecr create-repository `
  --repository-name pune-real-estate-api `
  --region ap-south-1

# Note the repositoryUri from output, it looks like:
# 123456789012.dkr.ecr.ap-south-1.amazonaws.com/pune-real-estate-api

# Login to ECR
$ECR_URI = "123456789012.dkr.ecr.ap-south-1.amazonaws.com"
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $ECR_URI

# Tag and push
docker tag pune-real-estate-api:latest "$ECR_URI/pune-real-estate-api:latest"
docker push "$ECR_URI/pune-real-estate-api:latest"
```

### Step 5.2 — Create ECS Cluster
```powershell
aws ecs create-cluster `
  --cluster-name pune-api-cluster `
  --region ap-south-1
```

Or via console: ECS → Create Cluster → Cluster name: `pune-api-cluster` → Networking only (Fargate) → Create.

### Step 5.3 — Create Task Definition

Save this as `deployment/ecs/task-definition.json`:
```json
{
  "family": "pune-api-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "pune-api",
      "image": "ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/pune-real-estate-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "MODEL_PATH", "value": "/app/models/best_model.pkl"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pune-api",
          "awslogs-region": "ap-south-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 30
      }
    }
  ]
}
```

Register it:
```powershell
aws ecs register-task-definition `
  --cli-input-json file://deployment/ecs/task-definition.json `
  --region ap-south-1
```

### Step 5.4 — Create Application Load Balancer
1. EC2 Console → Load Balancers → Create Load Balancer → Application Load Balancer
2. Name: `pune-api-alb`
3. Scheme: Internet-facing
4. IP address type: IPv4
5. Listeners: HTTP:80, HTTPS:443
6. Availability Zones: Select at least 2
7. Security group: Allow 80, 443 inbound from 0.0.0.0/0
8. Target group: Create new → `pune-api-tg` → Protocol: HTTP → Port: 8000 → Health check path: `/health`

### Step 5.5 — Create ECS Service
```powershell
aws ecs create-service `
  --cluster pune-api-cluster `
  --service-name pune-api-service `
  --task-definition pune-api-task `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxx,subnet-yyyy],securityGroups=[sg-xxxx],assignPublicIp=ENABLED}" `
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:ap-south-1:ACCOUNT:targetgroup/pune-api-tg/xxxx,containerName=pune-api,containerPort=8000" `
  --region ap-south-1
```

### Step 5.6 — Add SSL via ACM
1. AWS Console → Certificate Manager → Request certificate → Public certificate
2. Domain name: `api.yourdomain.com`
3. Validation: DNS validation
4. Add the CNAME record to your DNS (Route 53 can do this automatically)
5. Wait for status: Issued
6. Go to your ALB → Listeners → HTTPS:443 → Add certificate → Select the ACM cert

### Step 5.7 — Verify ECS Deployment
```powershell
# Get ALB DNS name
aws elbv2 describe-load-balancers --names pune-api-alb --query "LoadBalancers[0].DNSName" --output text

# Test via ALB DNS (before custom domain setup)
curl http://LOAD_BALANCER_DNS/health
```

---

## 6. Kubernetes Production Setup

### Prerequisites
- Install kubectl: `winget install Kubernetes.kubectl`
- Install AWS eksctl: download from github.com/weaveworks/eksctl/releases
- Or use a local cluster: `winget install Rancher.Minikube`

### Step 6.1 — Create Kubernetes Cluster on AWS EKS
```powershell
eksctl create cluster `
  --name pune-api-cluster `
  --region ap-south-1 `
  --nodegroup-name pune-api-nodes `
  --node-type t3.small `
  --nodes 2 `
  --nodes-min 1 `
  --nodes-max 4 `
  --managed

# Configure kubectl to use this cluster
aws eks update-kubeconfig --name pune-api-cluster --region ap-south-1

# Verify
kubectl get nodes
```

### Step 6.2 — Create Kubernetes Secret for Docker Image Pull
```powershell
# Create ECR pull secret
kubectl create secret docker-registry ecr-secret `
  --docker-server=ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com `
  --docker-username=AWS `
  --docker-password=$(aws ecr get-login-password --region ap-south-1)
```

### Step 6.3 — Deployment Manifest
Save as `deployment/kubernetes/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pune-api
  labels:
    app: pune-api
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pune-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during update
      maxUnavailable: 0  # Never go below desired replicas during update
  template:
    metadata:
      labels:
        app: pune-api
    spec:
      imagePullSecrets:
        - name: ecr-secret
      containers:
        - name: pune-api
          image: ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/pune-real-estate-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: APP_ENV
              value: "production"
            - name: MODEL_PATH
              value: "/app/models/best_model.pkl"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 60
            periodSeconds: 30
            failureThreshold: 3
```

### Step 6.4 — Service Manifest
Save as `deployment/kubernetes/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: pune-api-service
spec:
  selector:
    app: pune-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP  # Internal only — Ingress handles external access
```

### Step 6.5 — Ingress Manifest
Save as `deployment/kubernetes/ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pune-api-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - api.yourdomain.com
      secretName: pune-api-tls
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pune-api-service
                port:
                  number: 80
```

### Step 6.6 — Install Nginx Ingress Controller and cert-manager
```powershell
# Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# cert-manager (for Let's Encrypt TLS)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Save as `deployment/kubernetes/clusterissuer.yaml`:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: shadrack.n159@gmail.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

### Step 6.7 — Deploy Everything
```powershell
kubectl apply -f deployment/kubernetes/clusterissuer.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml

# Monitor rollout
kubectl rollout status deployment/pune-api

# Check pods
kubectl get pods -l app=pune-api

# Check ingress (get the external IP)
kubectl get ingress pune-api-ingress
```

### Step 6.8 — Auto-scaling
```powershell
# Horizontal Pod Autoscaler: scale up when CPU > 70%
kubectl autoscale deployment pune-api `
  --min=2 `
  --max=10 `
  --cpu-percent=70

# Check HPA status
kubectl get hpa
```

---

## 7. GitHub Actions Full CI/CD

Save this as `.github/workflows/deploy.yml`:

```yaml
name: CI/CD Pipeline — Pune Real Estate API

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  DOCKER_IMAGE: ${{ secrets.DOCKER_USERNAME }}/pune-real-estate-api

jobs:
  # ─────────────────────────────────────────
  # JOB 1: Test
  # ─────────────────────────────────────────
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/ -v --tb=short
        continue-on-error: false

  # ─────────────────────────────────────────
  # JOB 2: Build and Push Docker Image
  # ─────────────────────────────────────────
  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.DOCKER_IMAGE }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: deployment/docker/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ─────────────────────────────────────────
  # JOB 3: Deploy to EC2
  # ─────────────────────────────────────────
  deploy-ec2:
    name: Deploy to AWS EC2
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            # Pull latest image
            docker pull ${{ env.DOCKER_IMAGE }}:latest

            # Stop and remove old container
            docker stop pune_api || true
            docker rm pune_api || true

            # Start new container
            docker run -d \
              --name pune_api \
              --restart unless-stopped \
              -p 8000:8000 \
              -v ~/pune_app/models:/app/models:ro \
              -e APP_ENV=production \
              ${{ env.DOCKER_IMAGE }}:latest

            # Wait for health check
            sleep 30
            curl -f http://localhost:8000/health || exit 1

            # Clean up old images
            docker image prune -f

      - name: Verify deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.EC2_HOST }}/health

  # ─────────────────────────────────────────
  # JOB 4: Deploy to ECS Fargate (optional)
  # ─────────────────────────────────────────
  deploy-ecs:
    name: Deploy to AWS ECS Fargate
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Push to ECR
        run: |
          ECR_URI=${{ steps.login-ecr.outputs.registry }}/pune-real-estate-api
          docker pull ${{ env.DOCKER_IMAGE }}:latest
          docker tag ${{ env.DOCKER_IMAGE }}:latest $ECR_URI:latest
          docker push $ECR_URI:latest

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster pune-api-cluster \
            --service pune-api-service \
            --force-new-deployment \
            --region ap-south-1

      - name: Wait for ECS deployment
        run: |
          aws ecs wait services-stable \
            --cluster pune-api-cluster \
            --services pune-api-service \
            --region ap-south-1
```

### All Required GitHub Secrets Summary
```
DOCKER_USERNAME       → Your Docker Hub username
DOCKER_PASSWORD       → Docker Hub access token
EC2_HOST              → EC2 Elastic IP or domain name
EC2_USER              → ubuntu
EC2_SSH_KEY           → Full content of your .pem file
AWS_ACCESS_KEY_ID     → IAM access key
AWS_SECRET_ACCESS_KEY → IAM secret key
```

---

## 8. Monitoring Setup

### CloudWatch Logs (EC2 with Docker)
```bash
# On EC2: Install CloudWatch agent
sudo apt-get install -y awslogs

# Configure log group
sudo tee /etc/awslogs/awslogs.conf > /dev/null <<'EOF'
[general]
state_file = /var/awslogs/state/agent-state

[/docker/pune-api]
file = /var/lib/docker/containers/*/*.log
log_group_name = /pune-api/docker
log_stream_name = {instance_id}
datetime_format = %Y-%m-%dT%H:%M:%S
EOF

sudo systemctl start awslogsd
sudo systemctl enable awslogsd
```

### CloudWatch Alarms
```powershell
# 5xx Error Rate Alarm (triggers if >5 errors in 5 minutes)
aws cloudwatch put-metric-alarm `
  --alarm-name "pune-api-5xx-errors" `
  --alarm-description "API returning 5xx errors" `
  --metric-name "5XXError" `
  --namespace "AWS/ApplicationELB" `
  --statistic Sum `
  --period 300 `
  --threshold 5 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 1 `
  --alarm-actions "arn:aws:sns:ap-south-1:ACCOUNT_ID:alerts" `
  --region ap-south-1

# High Response Time Alarm (triggers if P99 > 5 seconds)
aws cloudwatch put-metric-alarm `
  --alarm-name "pune-api-high-latency" `
  --alarm-description "API response time too high" `
  --metric-name "TargetResponseTime" `
  --namespace "AWS/ApplicationELB" `
  --statistic p99 `
  --period 300 `
  --threshold 5 `
  --comparison-operator GreaterThanThreshold `
  --evaluation-periods 2 `
  --alarm-actions "arn:aws:sns:ap-south-1:ACCOUNT_ID:alerts" `
  --region ap-south-1
```

### SNS Email Alert Setup
```powershell
# Create SNS topic for alerts
aws sns create-topic --name alerts --region ap-south-1

# Subscribe your email
aws sns subscribe `
  --topic-arn "arn:aws:sns:ap-south-1:ACCOUNT_ID:alerts" `
  --protocol email `
  --notification-endpoint shadrack.n159@gmail.com `
  --region ap-south-1
# Check email and confirm subscription
```

### Application-Level Logging
Add to `src/api/fastapi_app.py` to log every prediction:

```python
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PropertyInput):
    start = time.time()
    # ... existing prediction code ...
    duration_ms = (time.time() - start) * 1000
    logger.info(
        f"PREDICT area={payload.area_sqft} "
        f"location={payload.location} "
        f"predicted={result.predicted_price_lakhs}L "
        f"duration={duration_ms:.1f}ms"
    )
    return result
```

### Dashboard: CloudWatch Custom Dashboard
```powershell
aws cloudwatch put-dashboard `
  --dashboard-name "PuneAPIMonitoring" `
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "title": "API Request Count",
          "metrics": [["AWS/ApplicationELB","RequestCount","LoadBalancer","app/pune-api-alb/xxx"]],
          "period": 300
        }
      },
      {
        "type": "metric",
        "properties": {
          "title": "5XX Error Rate",
          "metrics": [["AWS/ApplicationELB","HTTPCode_Target_5XX_Count","LoadBalancer","app/pune-api-alb/xxx"]],
          "period": 300
        }
      }
    ]
  }' `
  --region ap-south-1
```

---

## 9. Security Hardening

### 9.1 — API Key Authentication
Add to `src/api/fastapi_app.py`:
```python
from fastapi import Security
from fastapi.security import APIKeyHeader
import os

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
VALID_API_KEY = os.getenv("API_KEY", "")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != VALID_API_KEY or not VALID_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Add dependency to predict endpoint:
@app.post("/predict", dependencies=[Depends(verify_api_key)])
def predict(payload: PropertyInput):
    ...
```

Client must include header: `X-API-Key: your-api-key`

### 9.2 — Rate Limiting
Install: `pip install slowapi`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("60/minute")  # 60 requests per minute per IP
async def predict(request: Request, payload: PropertyInput):
    ...
```

### 9.3 — Input Validation (already in Pydantic schema)
The `PropertyInput` Pydantic model already validates:
- `area_sqft > 0` (rejects negative areas)
- `amenity_score` in [0,7]
- All `has_*` fields in [0,1]

Add to reject obviously wrong inputs:
```python
area_sqft: float = Field(..., gt=0, le=100000, description="Area must be 1-100,000 sqft")
```

### 9.4 — HTTPS Only (Nginx config)
```nginx
# In Nginx config, force HTTPS redirect:
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 9.5 — Security Group Rules (EC2)
```
Inbound:
- Port 22 (SSH): Your IP only (e.g., 203.x.x.x/32)
- Port 80 (HTTP): 0.0.0.0/0 (redirects to HTTPS)
- Port 443 (HTTPS): 0.0.0.0/0

Outbound:
- All traffic: 0.0.0.0/0 (EC2 needs internet for Docker pulls, pip, etc.)
```

**Never open port 8000 to the internet.** Nginx proxies 80/443 → 8000 internally.

### 9.6 — Docker Image Security
```dockerfile
# Use specific version tag (not :latest) for base image in production
FROM python:3.10.14-slim

# Run as non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

---

## 10. Scaling Strategy

### Vertical Scaling (Scale Up — more powerful single server)
| EC2 Type | vCPU | RAM | Use Case |
|---|---|---|---|
| t3.micro | 2 | 1GB | Development only |
| t3.small | 2 | 2GB | Low traffic production (<100 req/min) |
| t3.medium | 2 | 4GB | Medium traffic (<500 req/min) |
| t3.large | 2 | 8GB | High traffic (<2000 req/min) |
| c5.xlarge | 4 | 8GB | CPU-intensive ML inference |

**How to scale up EC2:** Stop instance → Change instance type → Start. No data loss. ~3 minutes downtime.

### Horizontal Scaling (Scale Out — more instances)

**For ECS Fargate:**
```powershell
# Register auto scaling target
aws application-autoscaling register-scalable-target `
  --service-namespace ecs `
  --scalable-dimension ecs:service:DesiredCount `
  --resource-id service/pune-api-cluster/pune-api-service `
  --min-capacity 1 `
  --max-capacity 10

# Scale up when CPU > 70% for 2 minutes
aws application-autoscaling put-scaling-policy `
  --policy-name cpu-scaling `
  --service-namespace ecs `
  --resource-id service/pune-api-cluster/pune-api-service `
  --scalable-dimension ecs:service:DesiredCount `
  --policy-type TargetTrackingScaling `
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

**For Kubernetes (already configured in deployment.yaml):**
```powershell
kubectl autoscale deployment pune-api --min=2 --max=10 --cpu-percent=70
```

### Uvicorn Workers
Increase workers for better CPU utilization on multi-core instances:
```bash
# For t3.medium (2 vCPU): 2 workers
uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 2

# For c5.xlarge (4 vCPU): 4 workers  
uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
```

Rule of thumb: workers = (2 × CPU_cores) + 1

---

## 11. Disaster Recovery

### Backup Strategy

**Model file backup to S3 (run after every model retrain):**
```powershell
# Create S3 bucket
aws s3 mb s3://pune-api-model-backup --region ap-south-1

# Upload model
aws s3 cp models/best_model.pkl s3://pune-api-model-backup/models/best_model_$(Get-Date -Format 'yyyyMMdd_HHmmss').pkl

# List all backups
aws s3 ls s3://pune-api-model-backup/models/
```

**Automated backup via cron (on EC2):**
```bash
# Add to crontab: crontab -e
0 2 * * 0  # Every Sunday at 2am
aws s3 cp ~/pune_app/models/best_model.pkl \
  s3://pune-api-model-backup/models/best_model_$(date +%Y%m%d).pkl
```

### Rollback Procedure

**Rollback Docker image to previous version (EC2):**
```bash
# List available image tags on Docker Hub
# Pull specific previous version
docker pull YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:sha-abc1234

# Stop current container
docker stop pune_api && docker rm pune_api

# Start with previous image
docker run -d \
  --name pune_api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v ~/pune_app/models:/app/models:ro \
  YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:sha-abc1234

# Verify rollback
curl http://localhost:8000/health
```

**Rollback ECS to previous task definition:**
```powershell
# List task definition revisions
aws ecs list-task-definitions --family-prefix pune-api-task

# Update service to use previous revision (e.g., revision 3)
aws ecs update-service `
  --cluster pune-api-cluster `
  --service pune-api-service `
  --task-definition pune-api-task:3

# Wait for rollback
aws ecs wait services-stable --cluster pune-api-cluster --services pune-api-service
```

**Rollback Kubernetes deployment:**
```powershell
# Check rollout history
kubectl rollout history deployment/pune-api

# Rollback to previous revision
kubectl rollout undo deployment/pune-api

# Rollback to specific revision
kubectl rollout undo deployment/pune-api --to-revision=2

# Monitor rollback
kubectl rollout status deployment/pune-api
```

### Disaster Recovery Time Objectives
| Scenario | Recovery Procedure | RTO |
|---|---|---|
| Bad Docker image deployed | Rollback to previous image tag | 5 minutes |
| EC2 instance terminated | Launch new EC2, pull Docker image, start | 15 minutes |
| Model file corrupted | Download backup from S3, restart container | 10 minutes |
| Database corrupted (MLflow) | Restore from S3 backup or recreate from git | 30 minutes |
| Entire AWS region down | Redeploy in different region | 2 hours |

---

## 12. Cost Estimation

### Option A — EC2 (t3.small, ap-south-1)
| Resource | Monthly Cost (USD) |
|---|---|
| EC2 t3.small (24/7) | ~$15 |
| Elastic IP | $0 (free when attached) |
| EBS Storage (20GB gp3) | ~$2 |
| Data transfer (5GB/month) | ~$0.50 |
| Route 53 (domain routing) | ~$0.50 |
| **Total** | **~$18/month** |

### Option B — ECS Fargate (512 CPU / 1GB RAM, 1 task)
| Resource | Monthly Cost (USD) |
|---|---|
| Fargate vCPU (0.5 vCPU × 730h) | ~$15 |
| Fargate Memory (1GB × 730h) | ~$4 |
| Application Load Balancer | ~$16 |
| ECR storage (image) | ~$1 |
| Data transfer | ~$1 |
| **Total** | **~$37/month** |

### Option C — EKS Kubernetes (2 t3.small nodes)
| Resource | Monthly Cost (USD) |
|---|---|
| EKS Cluster | $73 |
| 2× t3.small nodes | ~$30 |
| Load Balancer | ~$16 |
| **Total** | **~$119/month** |

### Recommendation
- **Development / portfolio**: EC2 t3.small (~$18/month) — cheapest, easiest to manage
- **Production without ops burden**: ECS Fargate (~$37/month) — serverless, auto-scaling
- **Enterprise / team production**: EKS (~$119/month) — full orchestration, multi-team

**Free Tier Note:** New AWS accounts get 750 hours/month of t2.micro free for 12 months. Run the API on t2.micro for zero cost during the free tier period.

---

## 13. Maintenance Guide

### 13.1 — How to Retrain the Model with New Data

**Step 1:** Add new data to `data/raw/` (new XLSX or CSV rows)

**Step 2:** Run the pipeline
```powershell
# Rerun only changed stages
dvc repro

# Or run manually:
python src/data/preprocess.py
python src/models/train.py
```

**Step 3:** Check MLflow to verify new model beats old one
```powershell
# Start MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
# Open http://localhost:5000 and compare runs
```

**Step 4:** If new model is better, rebuild Docker image
```powershell
docker build -t YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.1.0 .
docker push YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.1.0
```

**Step 5:** Update production
```powershell
# On EC2:
ssh ubuntu@YOUR_EC2_IP
docker pull YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.1.0
docker stop pune_api && docker rm pune_api
docker run -d --name pune_api --restart unless-stopped -p 8000:8000 \
  -v ~/pune_app/models:/app/models:ro \
  YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.1.0
```

### 13.2 — How to Update the API (Zero Downtime)

**Zero downtime = run new container before stopping old one:**
```bash
# On EC2 — Blue/Green deployment
# Step 1: Start new container on a different port (8001)
docker run -d --name pune_api_new -p 8001:8000 \
  YOUR_DOCKERHUB_USERNAME/pune-real-estate-api:v1.2.0

# Step 2: Wait for health check to pass
sleep 30 && curl http://localhost:8001/health

# Step 3: Update Nginx to point to new port
sudo sed -i 's/proxy_pass http:\/\/127.0.0.1:8000/proxy_pass http:\/\/127.0.0.1:8001/' \
  /etc/nginx/sites-available/pune_api
sudo systemctl reload nginx

# Step 4: Stop old container
docker stop pune_api && docker rm pune_api

# Step 5: Rename new container
docker rename pune_api_new pune_api
```

**For ECS Fargate:** Just push a new image and run `aws ecs update-service --force-new-deployment`. ECS handles rolling replacement automatically.

**For Kubernetes:** `kubectl set image deployment/pune-api pune-api=NEW_IMAGE:TAG`. Kubernetes performs rolling update with zero downtime (maxUnavailable=0).

### 13.3 — Log Checking and Troubleshooting

```bash
# Docker logs (last 100 lines)
docker logs pune_api --tail 100

# Follow live logs
docker logs pune_api -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# ECS logs (CloudWatch)
aws logs tail /ecs/pune-api --follow --region ap-south-1
```

### 13.4 — Model Versioning Convention
```
best_model.pkl        → Current production model (always latest)
models/archive/
  best_model_v1.0.pkl  → Original GBM trained June 2026
  best_model_v1.1.pkl  → Retrained with 300 records
  best_model_v2.0.pkl  → Major feature engineering change
```

Bump version in `src/api/fastapi_app.py`:
```python
app = FastAPI(title="...", version="1.1.0")
# Also update in PredictionResponse:
model_version="1.1.0"
```

### 13.5 — Weekly Health Checks
Run these checks every Monday:
```powershell
# 1. API health
curl https://api.yourdomain.com/health

# 2. Make a test prediction
curl -X POST https://api.yourdomain.com/predict `
  -H "Content-Type: application/json" `
  -d '{"area_sqft":1000,"amenity_score":4,"has_clubhouse":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'

# 3. Check Docker container status (on EC2)
docker ps -a

# 4. Check disk space (on EC2)
df -h

# 5. Check CloudWatch for errors
aws cloudwatch get-metric-statistics `
  --namespace AWS/ApplicationELB `
  --metric-name HTTPCode_Target_5XX_Count `
  --start-time (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ssZ") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ") `
  --period 604800 `
  --statistics Sum `
  --region ap-south-1
```
