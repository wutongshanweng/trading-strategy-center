#!/usr/bin/env bash
# ============================================================
# Trading Strategy Center — 一键启动脚本 (Local Dev)
# ============================================================
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
error(){ echo -e "${RED}[✗]${NC} $*"; }
info() { echo -e "${CYAN}[→]${NC} $*"; }

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════╗"
echo "║    Trading Strategy Center — 一键启动          ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# --------------------------------------------------
# 1. Python 环境检查
# --------------------------------------------------
info "Step 1/7: 检查 Python 环境..."
PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
    error "Python 未安装，请先安装 Python 3.10+"
    exit 1
fi
PY_VER=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
info "  Python $PY_VER  ✓"

# --------------------------------------------------
# 2. 虚拟环境
# --------------------------------------------------
info "Step 2/7: 设置虚拟环境..."
if [ ! -d "venv" ]; then
    "$PYTHON" -m venv venv
    log "  虚拟环境已创建"
else
    info "  虚拟环境已存在"
fi
source venv/bin/activate
log "  虚拟环境已激活"

# --------------------------------------------------
# 3. Python 依赖
# --------------------------------------------------
info "Step 3/7: 安装 Python 依赖..."
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]" || pip install --quiet -r requirements.txt 2>/dev/null || true
log "  依赖安装完成"

# --------------------------------------------------
# 4. Node.js 前端依赖
# --------------------------------------------------
info "Step 4/7: 安装前端依赖..."
cd "$APP_DIR/frontend"
if command -v pnpm &>/dev/null; then
    pnpm install --silent
elif command -v npm &>/dev/null; then
    npm install --silent
else
    warn "  Node.js/npm 未安装，跳过前端依赖"
fi
cd "$APP_DIR"
log "  前端依赖安装完成"

# --------------------------------------------------
# 5. 环境配置文件
# --------------------------------------------------
info "Step 5/7: 环境配置..."
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# Trading Strategy Center — Local Dev Config
DB_HOST=localhost
DB_PORT=5432
DB_USER=trading
DB_PASS=trading_pass
DB_NAME=trading_strategy_center
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
ENVEOF
    log "  .env 文件已创建 (默认本地配置)"
else
    info "  .env 文件已存在"
fi

# --------------------------------------------------
# 6. 基础设施检测（可选）
# --------------------------------------------------
info "Step 6/7: 基础设施检测..."
docker_check() {
    command -v docker &>/dev/null && info "  Docker: 可用" || warn "  Docker: 未安装 (数据库需手动启动)"
}
docker_check

# --------------------------------------------------
# 7. 启动服务
# --------------------------------------------------
info "Step 7/7: 启动服务..."
echo ""
echo -e "${CYAN}──────────────────────────────────────────────${NC}"
echo -e "${GREEN}  系统准备就绪！${NC}"
echo -e "${CYAN}──────────────────────────────────────────────${NC}"
echo ""
echo -e "  后端 API:  ${GREEN}http://localhost:8000${NC}"
echo -e "  前端界面:  ${GREEN}http://localhost:3000${NC}"
echo -e "  API 文档:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "  启动方式:"
echo -e "    ${YELLOW}方式1 (Docker):${NC}  docker compose up --build -d"
echo -e "    ${YELLOW}方式2 (本地):${NC}    source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo -e "    ${YELLOW}方式3 (前端):${NC}    cd frontend && npm run dev"
echo ""

# Check if docker compose is available
if command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    echo -e "${YELLOW}是否启动 Docker 服务? (y/n)${NC}"
    read -r -t 10 ans || true
    if [ "${ans:-n}" = "y" ]; then
        info "启动 Docker Compose..."
        docker compose up --build -d
        log "Docker 服务已启动"
    else
        info "跳过 Docker 启动"
        echo -e "  手动启动: ${CYAN}docker compose up --build -d${NC}"
    fi
fi

echo ""
log "一键启动完成！"
echo ""
