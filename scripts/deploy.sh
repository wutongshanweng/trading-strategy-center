#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/trading-strategy-center"
BACKUP_DIR="/opt/backups/trading-strategy-center"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
error_exit() { log "ERROR: $*"; exit 1; }

cd "$APP_DIR"
command -v docker >/dev/null 2>&1 || error_exit "docker not found"
command -v docker-compose >/dev/null 2>&1 || error_exit "docker-compose not found"

log "Backing up..."
mkdir -p "$BACKUP_DIR/pre-deploy-${TIMESTAMP}"
cp docker-compose.yml nginx.conf .env "$BACKUP_DIR/pre-deploy-${TIMESTAMP}/" 2>/dev/null || true

log "Pulling latest..."
git pull origin main || log "git pull skipped"

log "Deploying..."
docker-compose down --remove-orphans || true
docker-compose up --build -d

log "Health check..."
for i in $(seq 1 30); do
    sleep 5
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    [ "$HTTP_CODE" = "200" ] && log "OK" && exit 0
done
error_exit "Health check failed"
