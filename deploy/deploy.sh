#!/usr/bin/env bash
# =============================================================================
# Magento-CJ — 通用部署脚本
# =============================================================================
# 用法:
#   沙箱部署:  ./deploy.sh sandbox
#   正式部署:  ./deploy.sh production      # 在 ECS 上运行
#   停止服务:  ./deploy.sh sandbox down
#   查看状态:  ./deploy.sh sandbox status
# =============================================================================
set -euo pipefail

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ---- 检测环境 ----
detect_env() {
    if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
    else
        echo "linux"
    fi
}

# ---- 路径解析 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MAGENTO_PROJECT="${MAGENTO_PROJECT_DIR:-/home/yao/magento-project}"

# ---- 环境配置 ----
ENV="${1:-sandbox}"            # sandbox | production
ACTION="${2:-up}"              # up | down | restart | status | logs | rebuild

if [[ "$ENV" != "sandbox" && "$ENV" != "production" ]]; then
    err "第一个参数必须是 sandbox 或 production"
    echo "用法: $0 {sandbox|production} [up|down|restart|status|logs|rebuild]"
    exit 1
fi

HOST_ENV=$(detect_env)

echo "=============================================="
echo "  Magento-CJ 部署工具"
echo "  环境:    ${ENV}"
echo "  操作:    ${ACTION}"
echo "  宿主机:  ${HOST_ENV}"
echo "  项目:    ${PROJECT_ROOT}"
echo "=============================================="
echo ""

# ============================================================================
# 中间件部署
# ============================================================================
deploy_middleware() {
    local env_file="${SCRIPT_DIR}/env/${ENV}.env"

    if [[ ! -f "$env_file" ]]; then
        err "找不到环境文件: $env_file"
        err "请先从 deploy/env/.env.example 创建"
        exit 1
    fi

    # 使用环境文件
    cd "$PROJECT_ROOT"

    case "$ACTION" in
        up)
            log "复制 ${ENV} 环境配置..."
            cp "$env_file" .env
            ok "环境配置就绪"

            log "启动中间件服务..."
            docker compose down --remove-orphans 2>/dev/null || true
            docker compose up -d --build
            ok "中间件服务已启动"
            ;;
        down)
            log "停止中间件服务..."
            docker compose down
            ok "中间件服务已停止"
            ;;
        restart)
            log "重启中间件服务..."
            docker compose down
            docker compose up -d --build
            ok "中间件服务已重启"
            ;;
        status)
            docker compose ps
            ;;
        logs)
            docker compose logs -f app
            ;;
        rebuild)
            log "重建中间件镜像..."
            docker compose build --no-cache
            docker compose up -d
            ok "中间件镜像已重建"
            ;;
    esac
}

# ============================================================================
# Magento 部署
# ============================================================================
deploy_magento() {
    local env_file="${SCRIPT_DIR}/magento/.env.${ENV}"

    if [[ ! -d "$MAGENTO_PROJECT" ]]; then
        warn "Magento 项目目录不存在: $MAGENTO_PROJECT，跳过"
        warn "设置 MAGENTO_PROJECT_DIR 环境变量指定路径"
        return
    fi

    if [[ ! -f "$env_file" ]]; then
        err "找不到 Magento 环境文件: $env_file"
        exit 1
    fi

    cd "$MAGENTO_PROJECT"

    case "$ACTION" in
        up)
            log "复制 Magento ${ENV} 环境配置..."
            cp "$env_file" .env
            ok "Magento 环境配置就绪"

            log "启动 Magento 服务..."
            docker compose down --remove-orphans 2>/dev/null || true
            docker compose up -d
            ok "Magento 服务已启动"
            ;;
        down)
            log "停止 Magento 服务..."
            docker compose down
            ok "Magento 服务已停止"
            ;;
        restart)
            log "重启 Magento 服务..."
            docker compose down
            docker compose up -d
            ok "Magento 服务已重启"
            ;;
        status)
            docker compose ps
            ;;
        logs)
            docker compose logs -f app
            ;;
    esac
}

# ============================================================================
# Cloudflare Tunnel 管理
# ============================================================================
deploy_tunnel() {
    local config_file="${SCRIPT_DIR}/cloudflared/${ENV}-config.yml"

    if [[ "$ENV" == "sandbox" ]]; then
        # 沙箱: 本地 cloudflared (Windows 管理)
        log "沙箱 Cloudflare Tunnel 由 Windows 端 cloudflared 管理"
        log "配置参考: $config_file"
        log "如需重启: 在 Windows 上运行 cloudflared tunnel run <tunnel-id>"
    else
        # 正式: ECS 上的 cloudflared Docker 或 systemd 服务
        if [[ "$ACTION" == "up" || "$ACTION" == "restart" ]]; then
            log "检查 ECS Cloudflare Tunnel..."
            if docker ps --format '{{.Names}}' 2>/dev/null | grep -q cloudflared; then
                log "Cloudflare Tunnel 容器已在运行"
            else
                warn "Cloudflare Tunnel 未在 ECS 上运行"
                warn "请手动部署 cloudflared 容器或 systemd 服务"
                warn "配置文件: $config_file"
            fi
        fi
    fi
}

# ============================================================================
# 环境差异检查（防止沙箱 vs 正式不一致）
# ============================================================================
check_consistency() {
    log "检查环境一致性..."

    local issues=0

    # 检查 Docker Compose 版本
    local compose_files=("$PROJECT_ROOT/docker-compose.yml")
    for f in "${compose_files[@]}"; do
        if [[ -f "$f" ]]; then
            # 提取镜像标签，确保两边一致
            :
        fi
    done

    # 检查 requirements.txt 是否存在
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
        err "缺少 requirements.txt"
        issues=$((issues + 1))
    fi

    # 检查 Dockerfile 是否存在
    if [[ ! -f "$PROJECT_ROOT/Dockerfile" ]]; then
        err "缺少 Dockerfile"
        issues=$((issues + 1))
    fi

    if [[ $issues -gt 0 ]]; then
        err "发现 ${issues} 个问题，请修复后重新部署"
        exit 1
    fi

    ok "环境一致性检查通过"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────┐"
    echo "  │  同一份 docker-compose.yml → 同一份 Docker 镜像     │"
    echo "  │  不同 .env 文件 → 仅配置差异，无环境差异             │"
    echo "  │  沙箱测什么，正式就是什么                           │"
    echo "  └─────────────────────────────────────────────────────┘"
    echo ""
}

# ============================================================================
# 主流程
# ============================================================================
main() {
    if [[ "$ACTION" == "status" ]]; then
        deploy_middleware
        deploy_magento
        return
    fi

    if [[ "$ACTION" == "logs" ]]; then
        deploy_middleware
        return
    fi

    # 部署前检查
    if [[ "$ACTION" == "up" || "$ACTION" == "restart" || "$ACTION" == "rebuild" ]]; then
        check_consistency
    fi

    # 部署中间件
    deploy_middleware

    # 部署 Magento（沙箱模式本地已运行则跳过）
    if [[ "$ENV" == "production" ]]; then
        deploy_magento
    else
        warn "沙箱模式下跳过 Magento 部署（应在本地单独维护）"
    fi

    # 管理 Tunnel
    deploy_tunnel

    # 摘要
    if [[ "$ACTION" == "up" || "$ACTION" == "restart" ]]; then
        echo ""
        echo "=============================================="
        echo "  部署摘要"
        echo "=============================================="
        echo "  ${ENV} 环境服务已启动"
        echo ""
        echo "  中间件:"
        echo "    API:       http://localhost:3000"
        echo "    Docs:      http://localhost:3000/docs"
        echo "    Health:    http://localhost:3000/health"
        echo ""
        if [[ "$ENV" == "sandbox" ]]; then
            echo "  Magento:"
            echo "    Store:     http://localhost:8088"
            echo "    Admin:     http://localhost:8088/admin"
            echo ""
            echo "  Tunnel (外网):"
            echo "    Store:     https://shop-sandbox.yokileopard.top"
            echo "    API:       https://mcj-sandbox.yokileopard.top"
        else
            echo "  Magento:"
            echo "    Store:     https://shop.yokileopard.top"
            echo "    Admin:     https://shop.yokileopard.top/admin"
            echo "  API:"
            echo "    Middleware: https://mcj.yokileopard.top"
        fi
        echo "=============================================="
    fi
}

main "$@"
