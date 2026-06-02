#!/bin/bash
# =========================================================
# AWS EC2 Deployment Script — Pune Real Estate ML API
# Tested on: Ubuntu 22.04 LTS (t2.medium or t3.small)
# =========================================================
set -e

echo "============================================"
echo " Pune Real Estate MLOps — EC2 Setup Script "
echo "============================================"

# ── 1. System update ──
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv git docker.io docker-compose curl nginx

# ── 2. Enable Docker ──
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# ── 3. Clone your repo (update this URL after pushing to GitHub) ──
REPO_URL="https://github.com/YOUR_USERNAME/pune_real_estate.git"
APP_DIR="$HOME/pune_real_estate"

if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# ── 4. Python venv setup ──
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Run data pipeline and train model ──
echo "Running data pipeline..."
python src/data/preprocess.py

echo "Training model..."
python src/models/train.py

# ── 6. Start FastAPI via Docker Compose ──
echo "Building and starting Docker containers..."
cd deployment/docker
sudo docker-compose up --build -d
cd "$APP_DIR"

# ── 7. Nginx reverse proxy setup ──
NGINX_CONF="/etc/nginx/sites-available/pune_re_api"
sudo tee "$NGINX_CONF" > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /mlflow/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
    }
}
NGINX

sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "✅  DEPLOYMENT COMPLETE"
echo "   API  → http://$(curl -s ifconfig.me)/docs"
echo "   MLflow → http://$(curl -s ifconfig.me)/mlflow"
echo ""
echo "To check logs: sudo docker-compose -f deployment/docker/docker-compose.yml logs -f api"
