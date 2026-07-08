#!/bin/bash
# EGP-IMS 前端一键部署
# 用法: ./deploy.sh [saas|intranet|all]
# 默认: all
#
# Nginx 配置（服务器端）:
#   SaaS:     onemipham.com        → root /opt/egp-ims/saas/frontend
#   Intranet: rismedronxin.com     → alias /opt/egp-ims/intranet/frontend

set -e

SERVER="onemipham"
SAAS_PATH="/opt/egp-ims/saas/frontend/"
INTRANET_PATH="/opt/egp-ims/intranet/frontend/"
SAAS_URL="https://onemipham.com/saas/"
INTRANET_URL="https://rismedronxin.com/intranet/login"

TARGET="${1:-all}"

echo "=== EGP-IMS 前端部署 ==="

# 加载 nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 24

# 类型检查 + lint（一次性，两站共享源码）
echo ""
echo "--- 类型检查 + Lint ---"
npx vue-tsc --noEmit
npx eslint 'src/**/*.{ts,vue}' --max-warnings 100

deploy_saas() {
  echo ""
  echo "--- 构建 SaaS (onemipham.com/saas/) ---"
  rm -rf dist-saas
  VITE_BASE=/saas/ VITE_DEFAULT_LOCALE=en-US npx vite build --outDir dist-saas
  echo "--- 部署 → $SERVER:$SAAS_PATH ---"
  rsync -avz --delete dist-saas/ "$SERVER:$SAAS_PATH"
  rm -rf dist-saas
  echo "✅ SaaS 部署完成"
}

deploy_intranet() {
  echo ""
  echo "--- 构建 Intranet (rismedronxin.com/intranet/) ---"
  rm -rf dist-intranet
  VITE_BASE=/intranet/ npx vite build --outDir dist-intranet
  echo "--- 部署 → $SERVER:$INTRANET_PATH ---"
  rsync -avz --delete dist-intranet/ "$SERVER:$INTRANET_PATH"
  rm -rf dist-intranet
  echo "✅ Intranet 部署完成"
}

case "$TARGET" in
  saas)     deploy_saas ;;
  intranet) deploy_intranet ;;
  all)
    deploy_saas
    deploy_intranet
    ;;
  *)
    echo "用法: ./deploy.sh [saas|intranet|all]"
    exit 1
    ;;
esac

echo ""
echo "=== 验证 ==="
curl -skL -o /dev/null -w "SaaS:      %{http_code} $SAAS_URL\n" "$SAAS_URL"
curl -skL -o /dev/null -w "Intranet:  %{http_code} $INTRANET_URL\n" "$INTRANET_URL"
echo "=== 完成 ==="
