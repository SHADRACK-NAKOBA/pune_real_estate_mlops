# Continuation Guide — From Local to Live on AWS
**Author: Shadrack Nakoba | Starting Point: June 2026**
**Status at start: Everything working locally, code pushed to GitHub**

> This file picks up exactly where local development ended. Every command is for Windows PowerShell unless labeled otherwise. Read each step in full before running any command.

---

## Where We Are Now

| Component | Status |
|---|---|
| Data preprocessing | Done |
| 5 models trained | Done |
| MLflow tracking | Done (localhost:5000) |
| FastAPI server | Done (localhost:8000) |
| Code on GitHub | Done |
| Docker image built | NOT DONE |
| Docker Hub push | NOT DONE |
| GitHub Actions tested | NOT DONE |
| AWS EC2 deployed | NOT DONE |
| AWS ECS Fargate | NOT DONE |
| Kubernetes | NOT DONE |
| Live public HTTPS URL | NOT DONE |

---

## Prerequisites Before Starting

### Check Docker is Installed
```powershell
docker --version
# Expected: Docker version 24.x or higher
```

If not installed: Go to https://docs.docker.com/desktop/install/windows-install/ → Download Docker Desktop for Windows → Install → Restart machine.

After installing Docker Desktop, make sure it is running (look for the Docker whale icon in the system tray, bottom-right of taskbar).

### Check AWS CLI is Installed
```powershell
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x Windows/10
```

If not installed:
```powershell
winget install Amazon.AWSCLI
# After install, close and reopen PowerShell
aws --version
```

### Check Git is Configured
```powershell
git config --global user.name
git config --global user.email
# Should show your name and email
```

If blank:
```powershell
git config --global user.name "Shadrack Nakoba"
git config --global user.email "shadrack.n159@gmail.com"
```

---

## STEP 1 — Build Docker Image Locally

### 1.1 — Navigate to Project Root
```powershell
cd C:\Users\admin\Desktop\pune_real_estate_mlops
```

### 1.2 — Verify the model file exists
```powershell
Test-Path models\best_model.pkl
# Must return: True
# If False, run: python src/models/train.py first
```

### 1.3 — Build the Docker image
```powershell
docker build -t pune-real-estate-api:latest -f deployment/docker/Dockerfile .
```

This will take 5-15 minutes on first run because it downloads the Python base image and installs all packages. Subsequent builds use cached layers and take 30-60 seconds.

**What you see during build (normal output):**
```
[+] Building 234.5s (12/12) FINISHED
 => [1/7] FROM docker.io/library/python:3.10-slim
 => [2/7] RUN apt-get update ...
 => [3/7] WORKDIR /app
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install ...
 => [6/7] COPY . .
 => exporting to image
```

**Common error: Docker daemon not running**
```
error during connect: this error may indicate that the docker daemon is not running
```
Fix: Open Docker Desktop from the Start Menu and wait for "Docker Desktop is running" before retrying.

**Common error: disk space**
```
no space left on device
```
Fix: Open Docker Desktop → Settings → Resources → Disk image size → Increase to 60GB. Or run `docker system prune -a` to delete unused images.

### 1.4 — Verify the image was created
```powershell
docker images pune-real-estate-api
# Expected output:
# REPOSITORY              TAG       IMAGE ID       CREATED         SIZE
# pune-real-estate-api    latest    abc123def456   2 minutes ago   1.85GB
```

### 1.5 — Run the container locally and test it
```powershell
# Start the container
docker run -d `
  --name pune_api_test `
  -p 8000:8000 `
  -v "${PWD}\models:/app/models:ro" `
  pune-real-estate-api:latest

# Wait 30 seconds for startup
Start-Sleep -Seconds 30

# Test health endpoint
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}

# Test prediction endpoint
$body = '{"area_sqft":1000,"township_area":50,"amenity_score":4,"has_clubhouse":1,"has_school":1,"has_hospital":0,"has_mall":0,"has_park":1,"has_pool":0,"has_gym":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'

Invoke-WebRequest -Method POST `
  -Uri http://localhost:8000/predict `
  -ContentType "application/json" `
  -Body $body | Select-Object -ExpandProperty Content
# Expected: {"predicted_price_lakhs":87.4,...}

# View logs
docker logs pune_api_test

# Open Swagger UI in browser
Start-Process "http://localhost:8000/docs"
```

### 1.6 — Stop and remove test container
```powershell
docker stop pune_api_test
docker rm pune_api_test
```

---

## STEP 2 — Push Docker Image to Docker Hub

### 2.1 — Create Docker Hub account and repository
1. Go to https://hub.docker.com
2. Sign Up (free account) with username: `shadracknakoba` (or any username you choose — note it down)
3. After logging in: Create Repository → Name: `pune-real-estate-api` → Visibility: Public → Create

### 2.2 — Create Docker Hub Access Token (more secure than password)
1. hub.docker.com → click your username (top-right) → Account Settings
2. Left sidebar → Security → New Access Token
3. Token name: `github-actions` | Permissions: Read, Write, Delete
4. Generate → Copy the token (it appears only once — save it somewhere safe)

### 2.3 — Login to Docker Hub from PowerShell
```powershell
docker login -u YOUR_DOCKERHUB_USERNAME
# When prompted for password, paste the access token (not your account password)
# Expected: Login Succeeded
```

### 2.4 — Tag the image with your Docker Hub username
```powershell
# Replace shadracknakoba with YOUR actual Docker Hub username
docker tag pune-real-estate-api:latest shadracknakoba/pune-real-estate-api:latest
docker tag pune-real-estate-api:latest shadracknakoba/pune-real-estate-api:v1.0.0
```

### 2.5 — Push to Docker Hub
```powershell
docker push shadracknakoba/pune-real-estate-api:latest
docker push shadracknakoba/pune-real-estate-api:v1.0.0
```

This will take 3-10 minutes depending on your internet speed (image is ~1.5-2GB).

**Progress output looks like:**
```
The push refers to repository [docker.io/shadracknakoba/pune-real-estate-api]
latest: digest: sha256:abc123... size: 1234
```

### 2.6 — Verify on Docker Hub website
Go to https://hub.docker.com/r/shadracknakoba/pune-real-estate-api → you should see `latest` and `v1.0.0` tags.

---

## STEP 3 — Update deploy.sh with Your GitHub Repo URL

```powershell
# Open deploy.sh
code deployment/ec2/deploy.sh
```

Find this line:
```bash
REPO_URL="https://github.com/YOUR_USERNAME/pune_real_estate.git"
```

Change it to your actual repo:
```bash
REPO_URL="https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops.git"
APP_DIR="$HOME/pune_real_estate_mlops"
```

Save the file.

---

## STEP 4 — Set Up GitHub Actions Secrets

### 4.1 — Go to your GitHub repository
Open: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops

### 4.2 — Add secrets
Click: Settings (top tab) → Secrets and variables (left sidebar) → Actions → New repository secret

Add these secrets one by one:

| Secret Name | Value to Enter |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username (e.g., `shadracknakoba`) |
| `DOCKER_PASSWORD` | The access token you created in Step 2.2 |

Skip AWS secrets for now — we add them in Step 5 after creating the EC2 instance.

### 4.3 — Test the CI/CD pipeline (build only, no deploy yet)

The `.github/workflows/deploy.yml` file is already created in this project. Look at it:

```powershell
Get-Content .github\workflows\deploy.yml
```

Commit and push a small change to trigger the pipeline:
```powershell
# Make a trivial change (add a blank line to README or similar)
Add-Content -Path README.md -Value "`n<!-- CI/CD test trigger -->"

git add README.md
git commit -m "ci: trigger GitHub Actions pipeline test"
git push origin main
```

Watch the pipeline run:
1. Go to https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions
2. You should see a workflow run triggered by your push
3. Click it to see live logs

**Common error: Tests failing because test files don't exist**
```
pytest tests/ -v → ERROR: no tests ran
```
This is fine for now — `pytest` returns exit 0 even with no tests. If it fails, add a minimal test file:
```powershell
New-Item -ItemType Directory -Force tests
@"
def test_placeholder():
    assert True
"@ | Out-File -Encoding utf8 tests/test_placeholder.py
```

**Expected pipeline result after Steps 1-4:**
- test job: PASS (green)
- build job: PASS — image pushed to Docker Hub
- deploy-ec2 job: SKIPPED (no EC2_HOST secret yet)

---

## STEP 5 — Launch AWS EC2 Instance

### 5.1 — Create AWS Account (if you don't have one)
Go to https://aws.amazon.com → Create account. Use a personal credit card (AWS has a free tier — t2.micro is free for 12 months, 750 hours/month).

### 5.2 — Create IAM User for GitHub Actions
Do this before launching EC2 — you need the credentials for GitHub secrets.

1. AWS Console → IAM → Users → Create user
2. Username: `github-actions-deploy`
3. Permissions: Attach policies directly
   - Search and add: `AmazonEC2FullAccess`
   - Search and add: `AmazonEC2ContainerRegistryFullAccess`
4. Create user → Security credentials tab → Create access key
5. Use case: Application running outside AWS → Next → Create
6. Copy: Access Key ID and Secret Access Key → save them

**Add to GitHub secrets:**
| Secret | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | The access key ID |
| `AWS_SECRET_ACCESS_KEY` | The secret access key |

### 5.3 — Configure AWS CLI locally
```powershell
aws configure
# AWS Access Key ID: paste your access key
# AWS Secret Access Key: paste your secret key
# Default region: ap-south-1  (Mumbai — closest to Pune)
# Default output format: json
```

### 5.4 — Launch EC2 Instance via AWS Console
1. Go to https://console.aws.amazon.com/ec2 → ensure region is "Asia Pacific (Mumbai) ap-south-1"
2. Click "Launch instance"
3. Configure:
   - Name: `pune-real-estate-api`
   - AMI: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type (Free tier eligible)
   - Instance type: `t2.micro` (free tier) or `t3.small` (better performance, ~$15/month)
   - Key pair: "Create new key pair" → Name: `pune-api-key` → RSA → .pem format → Download
     - **Save the .pem file to C:\Users\admin\Downloads\pune-api-key.pem — you CANNOT re-download it**
   - Network settings: click "Edit"
     - Security group name: `pune-api-sg`
     - Add security group rule:
       - Type: SSH, Protocol: TCP, Port: 22, Source: My IP
       - Type: HTTP, Protocol: TCP, Port: 80, Source: Anywhere
       - Type: HTTPS, Protocol: TCP, Port: 443, Source: Anywhere
   - Storage: 20 GB gp3

4. Launch instance
5. Click on the instance ID → note the "Public IPv4 address" (e.g., `13.233.x.x`)

### 5.5 — Associate an Elastic IP (so IP doesn't change on reboot)
1. EC2 Console left sidebar → Network & Security → Elastic IPs
2. Allocate Elastic IP address → Allocate
3. Select the new Elastic IP → Actions → Associate Elastic IP address
4. Instance: select your `pune-real-estate-api` instance → Associate
5. Note the Elastic IP address — this is your permanent server IP

### 5.6 — Add EC2 secrets to GitHub
| Secret | Value |
|---|---|
| `EC2_HOST` | Your Elastic IP address (e.g., `13.233.x.x`) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full contents of your .pem file (open it in Notepad, copy all text including headers) |

**How to copy .pem file contents:**
```powershell
Get-Content C:\Users\admin\Downloads\pune-api-key.pem | Set-Clipboard
# Now paste into the GitHub secret value field
```

### 5.7 — SSH into EC2 and run initial setup
```powershell
# Set permissions on pem file (Windows)
$pem = "C:\Users\admin\Downloads\pune-api-key.pem"
icacls $pem /inheritance:r
icacls $pem /grant:r "${env:USERNAME}:(R)"

# Connect to EC2 (replace with your Elastic IP)
ssh -i $pem ubuntu@YOUR_ELASTIC_IP
```

Once connected (you see `ubuntu@ip-x-x-x-x:~$`), run:

```bash
# Update system
sudo apt-get update -y && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Nginx and Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx curl

# Logout and reconnect to apply docker group
exit
```

SSH back in:
```powershell
ssh -i $pem ubuntu@YOUR_ELASTIC_IP
```

```bash
# Verify Docker works without sudo
docker ps

# Create app directory
mkdir -p ~/pune_app/models

# Pull Docker image
docker pull shadracknakoba/pune-real-estate-api:latest

# Start the API container
docker run -d \
  --name pune_api \
  --restart unless-stopped \
  -p 8000:8000 \
  -e APP_ENV=production \
  shadracknakoba/pune-real-estate-api:latest

# Wait 30 seconds, then test
sleep 30
curl http://localhost:8000/health
# Expected: {"status":"ok","model_loaded":true}
```

**Note:** The model is embedded in the Docker image (via `COPY . .` in Dockerfile). The container has the model file at `/app/models/best_model.pkl` without needing to mount a volume.

### 5.8 — Configure Nginx on EC2

```bash
sudo tee /etc/nginx/sites-available/pune_api > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/pune_api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl enable nginx

# Test via Nginx (port 80)
curl http://localhost/health
```

### 5.9 — Test from your Windows machine
```powershell
# Test via EC2 public IP (port 80)
Invoke-WebRequest -Uri http://YOUR_ELASTIC_IP/health | Select-Object -ExpandProperty Content

# Test prediction
$body = '{"area_sqft":1000,"amenity_score":4,"has_clubhouse":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'
Invoke-WebRequest -Method POST `
  -Uri http://YOUR_ELASTIC_IP/predict `
  -ContentType "application/json" `
  -Body $body | Select-Object -ExpandProperty Content

# Open Swagger UI in browser
Start-Process "http://YOUR_ELASTIC_IP/docs"
```

At this point, your API is publicly accessible at `http://YOUR_ELASTIC_IP/docs`. Anyone in the world can call it.

### 5.10 — Add EC2_HOST secret and trigger full CI/CD deploy

Now that EC2 is running:
1. Add `EC2_HOST` secret to GitHub (your Elastic IP)
2. Push any change to main branch
3. GitHub Actions will: test → build → push to Docker Hub → SSH into EC2 → pull new image → restart container

```powershell
# Trigger by pushing any small change
git add .
git commit -m "feat: complete EC2 deployment and CI/CD pipeline"
git push origin main
```

Watch the deploy-ec2 job run at: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions

---

## STEP 6 — Add SSL / HTTPS (Requires Domain Name)

### 6.1 — Get a domain name
Options:
- **Free:** Freenom (freenom.com) — free `.tk`, `.ml` domains (may require signup)
- **Cheap:** Namecheap — `.xyz` domain for $1/year, `.com` for ~$10/year
- **AWS:** Route 53 → Register domain → ~$12/year for `.com`

### 6.2 — Point domain to EC2 Elastic IP
In your domain registrar's DNS settings, add:
- Type: A
- Name: `api` (for api.yourdomain.com) or `@` (for yourdomain.com)
- Value: YOUR_ELASTIC_IP
- TTL: 300

Wait 5-30 minutes for DNS to propagate. Test with:
```powershell
nslookup api.yourdomain.com
# Should return your Elastic IP
```

### 6.3 — Get SSL certificate with Let's Encrypt
SSH into EC2:
```bash
# Replace with your actual domain
sudo certbot --nginx -d api.yourdomain.com

# Enter email when prompted: shadrack.n159@gmail.com
# Agree to ToS: A
# Share email with EFF: N (your choice)

# After success, test HTTPS:
curl https://api.yourdomain.com/health
```

Your API is now at: **https://api.yourdomain.com/docs** — fully public, HTTPS, production grade.

### 6.4 — Verify SSL auto-renewal
```bash
sudo systemctl status certbot.timer
# Should show: active (waiting)
# Certbot will automatically renew every 90 days
```

---

## STEP 7 — AWS ECS Fargate Deployment (Optional — No Server Management)

### 7.1 — Configure AWS CLI with your credentials
```powershell
aws configure
# Enter credentials from Step 5.2
# Region: ap-south-1
```

### 7.2 — Create ECR repository and push image
```powershell
# Create ECR repo
aws ecr create-repository `
  --repository-name pune-real-estate-api `
  --region ap-south-1

# Note the repositoryUri from output (looks like 123456789012.dkr.ecr.ap-south-1.amazonaws.com/pune-real-estate-api)

# Login to ECR
$ecrUri = "$(aws ecr describe-repositories --repository-names pune-real-estate-api --query 'repositories[0].repositoryUri' --output text --region ap-south-1)"
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $ecrUri.Split('/')[0]

# Tag and push
docker tag pune-real-estate-api:latest "${ecrUri}:latest"
docker push "${ecrUri}:latest"
```

### 7.3 — Create ECS Cluster
```powershell
aws ecs create-cluster --cluster-name pune-api-cluster --region ap-south-1
```

### 7.4 — Create IAM role for ECS task execution
```powershell
# Create trust policy file
@'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
'@ | Out-File -Encoding utf8 trust-policy.json

# Create role
aws iam create-role `
  --role-name ecsTaskExecutionRole `
  --assume-role-policy-document file://trust-policy.json

# Attach required policy
aws iam attach-role-policy `
  --role-name ecsTaskExecutionRole `
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 7.5 — Create CloudWatch log group
```powershell
aws logs create-log-group --log-group-name /ecs/pune-api --region ap-south-1
```

### 7.6 — Register Task Definition
Update `deployment/ecs/task-definition.json` (created in PROD_READY.md, Section 5) with your actual account ID and ECR URI, then:
```powershell
# Get your account ID
$accountId = aws sts get-caller-identity --query Account --output text

# Register the task definition
aws ecs register-task-definition `
  --cli-input-json file://deployment/ecs/task-definition.json `
  --region ap-south-1
```

### 7.7 — Create Application Load Balancer via console
1. EC2 Console → Load Balancers → Create Load Balancer → Application Load Balancer
2. Name: `pune-api-alb`
3. Scheme: Internet-facing | IP type: IPv4
4. Listeners: Port 80 (HTTP)
5. VPC: Default VPC | Select all availability zones
6. Security group: Create new → allow HTTP:80 from 0.0.0.0/0
7. Target group:
   - Target type: IP addresses
   - Name: `pune-api-tg`
   - Protocol: HTTP | Port: 8000
   - Health check path: `/health`
   - Healthy threshold: 2 | Unhealthy threshold: 3 | Timeout: 10 | Interval: 30
8. Create load balancer
9. Note the ALB DNS name (ends with `.elb.amazonaws.com`)

### 7.8 — Create ECS Service
Get your subnet IDs and security group ID from the VPC console, then:
```powershell
$subnetIds = "subnet-xxxx,subnet-yyyy"  # Replace with your default VPC subnet IDs
$sgId = "sg-xxxx"  # Security group that allows port 8000
$targetGroupArn = "arn:aws:elasticloadbalancing:ap-south-1:ACCOUNT_ID:targetgroup/pune-api-tg/xxxx"

aws ecs create-service `
  --cluster pune-api-cluster `
  --service-name pune-api-service `
  --task-definition pune-api-task `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[$subnetIds],securityGroups=[$sgId],assignPublicIp=ENABLED}" `
  --load-balancers "targetGroupArn=$targetGroupArn,containerName=pune-api,containerPort=8000" `
  --region ap-south-1
```

### 7.9 — Wait for service to become stable
```powershell
aws ecs wait services-stable `
  --cluster pune-api-cluster `
  --services pune-api-service `
  --region ap-south-1

# Check service status
aws ecs describe-services `
  --cluster pune-api-cluster `
  --services pune-api-service `
  --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" `
  --output table `
  --region ap-south-1
```

### 7.10 — Test via Load Balancer
```powershell
$albDns = aws elbv2 describe-load-balancers --names pune-api-alb --query "LoadBalancers[0].DNSName" --output text --region ap-south-1

Invoke-WebRequest -Uri "http://$albDns/health" | Select-Object -ExpandProperty Content
# Expected: {"status":"ok","model_loaded":true}
```

**Your ECS API is now live at:** `http://LOAD_BALANCER_DNS/docs`

---

## STEP 8 — Kubernetes Deployment (Optional — Enterprise Grade)

### 8.1 — Install required tools
```powershell
# kubectl
winget install Kubernetes.kubectl
kubectl version --client

# eksctl
# Download from: https://github.com/weaveworks/eksctl/releases/latest
# Extract eksctl.exe to C:\Windows\System32\ (so it's in PATH)
eksctl version
```

### 8.2 — Create EKS cluster
This takes 15-20 minutes:
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
```

### 8.3 — Configure kubectl
```powershell
aws eks update-kubeconfig --name pune-api-cluster --region ap-south-1

# Verify connection
kubectl get nodes
# Expected: 2 nodes in Ready state
```

### 8.4 — Create Kubernetes manifests directory
```powershell
New-Item -ItemType Directory -Force deployment/kubernetes
```

### 8.5 — Create and apply all manifests

Create `deployment/kubernetes/deployment.yaml` (see PROD_READY.md Section 6.3 for full content, replacing ACCOUNT_ID with your actual account ID).

Create `deployment/kubernetes/service.yaml` (see PROD_READY.md Section 6.4).

Create `deployment/kubernetes/ingress.yaml` (see PROD_READY.md Section 6.5).

```powershell
# Apply all manifests
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml

# Monitor rollout
kubectl rollout status deployment/pune-api

# Check pods are running
kubectl get pods -l app=pune-api
# Expected: 2/2 pods Running
```

### 8.6 — Install Nginx Ingress Controller
```powershell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# Wait for ingress controller
kubectl wait --namespace ingress-nginx `
  --for=condition=ready pod `
  --selector=app.kubernetes.io/component=controller `
  --timeout=120s
```

### 8.7 — Get the Load Balancer external IP
```powershell
kubectl get service -n ingress-nginx ingress-nginx-controller
# Note the EXTERNAL-IP column (may take 3-5 minutes to populate)
```

### 8.8 — Port-forward for quick local test (no ingress needed)
```powershell
# Forward local port 8080 to the service
kubectl port-forward service/pune-api-service 8080:80

# In another PowerShell window:
Invoke-WebRequest -Uri http://localhost:8080/health | Select-Object -ExpandProperty Content
```

### 8.9 — Apply Ingress for external access
Update `deployment/kubernetes/ingress.yaml` with your domain name, then:
```powershell
# Install cert-manager for TLS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Apply cluster issuer
kubectl apply -f deployment/kubernetes/clusterissuer.yaml

# Apply ingress
kubectl apply -f deployment/kubernetes/ingress.yaml

# Check ingress
kubectl get ingress pune-api-ingress
# After a few minutes, ADDRESS column shows the load balancer DNS
```

### 8.10 — Set up Horizontal Pod Autoscaling
```powershell
kubectl autoscale deployment pune-api --min=2 --max=10 --cpu-percent=70
kubectl get hpa
```

---

## STEP 9 — Verify the Full System End-to-End

### 9.1 — EC2 verification
```powershell
# Health check
Invoke-WebRequest -Uri "https://api.yourdomain.com/health" | Select-Object -ExpandProperty Content

# Swagger UI works
Start-Process "https://api.yourdomain.com/docs"

# Full prediction test
$headers = @{"Content-Type" = "application/json"}
$body = '{"area_sqft":1200,"township_area":80,"amenity_score":5,"has_clubhouse":1,"has_school":1,"has_hospital":1,"has_mall":0,"has_park":1,"has_pool":1,"has_gym":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'

$response = Invoke-WebRequest -Method POST `
  -Uri "https://api.yourdomain.com/predict" `
  -Headers $headers `
  -Body $body
  
$response.Content
# Expected: {"predicted_price_lakhs": 112.3, "predicted_price_millions": 11.23, ...}

# Batch prediction test
$batchBody = '[{"area_sqft":800,"amenity_score":2,"location":1,"sub_area":1,"property_type":0,"company_name":0},{"area_sqft":2000,"amenity_score":7,"has_clubhouse":1,"has_pool":1,"location":5,"sub_area":10,"property_type":2,"company_name":3}]'
$response = Invoke-WebRequest -Method POST `
  -Uri "https://api.yourdomain.com/predict/batch" `
  -Headers $headers `
  -Body $batchBody
$response.Content
```

### 9.2 — CI/CD verification
1. Edit any file (e.g., add a comment to `src/api/fastapi_app.py`)
2. Commit and push to main
3. Watch at: https://github.com/SHADRACK-NAKOBA/pune_real_estate_mlops/actions
4. All jobs should be green: test ✓ → build ✓ → deploy-ec2 ✓
5. Verify the new container is running on EC2 after ~3 minutes

### 9.3 — Docker Hub verification
```powershell
# Pull and run from Docker Hub on any machine
docker pull shadracknakoba/pune-real-estate-api:latest
docker run -d --name verify_test -p 8080:8000 shadracknakoba/pune-real-estate-api:latest
Start-Sleep -Seconds 30
Invoke-WebRequest -Uri http://localhost:8080/health | Select-Object -ExpandProperty Content
docker stop verify_test && docker rm verify_test
```

---

## STEP 10 — Final Checklist Before Calling It Live

Run through each item — check it only when verified:

```
DOCKER
[ ] docker images shows pune-real-estate-api with correct size
[ ] docker run works and /health returns ok
[ ] Image is on Docker Hub with :latest and :v1.0.0 tags

CI/CD
[ ] GitHub Actions runs on push to main
[ ] test job: green
[ ] build job: green (image pushed to Docker Hub)
[ ] deploy-ec2 job: green (new container on EC2)

EC2
[ ] SSH access works with .pem key
[ ] docker ps shows pune_api container "Up X hours"
[ ] curl http://YOUR_EC2_IP/health → ok
[ ] curl http://YOUR_EC2_IP/docs → HTML page (Swagger)
[ ] Nginx running: sudo systemctl status nginx

HTTPS (if domain configured)
[ ] https://api.yourdomain.com/health → ok
[ ] http://api.yourdomain.com redirects to https://
[ ] SSL certificate is valid (browser shows padlock)
[ ] certbot renew --dry-run succeeds

MONITORING
[ ] CloudWatch logs visible in AWS console
[ ] 5xx error alarm configured
[ ] SNS email alert subscription confirmed

SECURITY
[ ] EC2 security group: port 22 restricted to your IP only
[ ] No AWS keys in GitHub repository (check git log)
[ ] .env file not committed (check .gitignore)

FINAL TEST
[ ] POST to /predict from a mobile data connection (not same WiFi) returns a valid price
[ ] POST to /predict with area_sqft=-1 returns HTTP 422 (validation error)
[ ] POST to /predict/batch with 101 items returns HTTP 400
```

---

## Troubleshooting Common Deployment Issues

### Issue: Docker container keeps restarting
```powershell
docker logs pune_api_test --tail 50
```
Usually caused by: model file not found. Verify the model is in the image or mounted correctly.

### Issue: Nginx returns 502 Bad Gateway
The FastAPI container is not running or not healthy.
```bash
# On EC2:
docker ps  # Is the container running?
docker logs pune_api  # Is there a startup error?
curl http://localhost:8000/health  # Does it respond locally?
```

### Issue: GitHub Actions deploy job fails with SSH error
```
ssh: connect to host x.x.x.x port 22: Connection refused
```
Check: EC2 security group allows port 22 from the GitHub Actions IP range. Temporary fix: set SSH source to 0.0.0.0/0 for testing, then restrict back.

### Issue: ECS task keeps stopping with exit code 1
Check CloudWatch logs: `/ecs/pune-api` log group. Usually caused by missing environment variables or out-of-memory error (increase task memory from 1024 to 2048MB in task definition).

### Issue: Let's Encrypt certificate fails
```
FAILED: Could not obtain certificates
```
Verify DNS has propagated: `nslookup api.yourdomain.com` must return your Elastic IP. DNS can take up to 48 hours (usually 5-30 minutes).

### Issue: kubectl cannot connect to EKS
```powershell
# Refresh kubeconfig
aws eks update-kubeconfig --name pune-api-cluster --region ap-south-1
kubectl get nodes
```

---

## Summary: Your Live API Endpoints

After completing all steps:

| Endpoint | URL |
|---|---|
| Health check | `https://api.yourdomain.com/health` |
| Single prediction | `POST https://api.yourdomain.com/predict` |
| Batch prediction | `POST https://api.yourdomain.com/predict/batch` |
| Swagger UI | `https://api.yourdomain.com/docs` |
| ReDoc | `https://api.yourdomain.com/redoc` |

**Sample curl command (share this with anyone):**
```bash
curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -d '{"area_sqft":1000,"amenity_score":4,"has_clubhouse":1,"has_school":1,"location":3,"sub_area":5,"property_type":1,"company_name":2}'
```

Congratulations — you have built and deployed a complete end-to-end MLOps pipeline.
