#!/bin/bash
# EGP-IMS Frontend 一键部署
# 用法: ./deploy.sh [saas|intranet|all]
# 默认: all

set -e

SERVER="onemipham"
SAAS_PATH="/opt/egp-ims/saas/frontend/dist/"
INTRANET_PATH="/opt/egp-ims/intranet/frontend/dist/"

TARGET="${1:-all}"

echo "=== EGP-IMS 前端部署 ==="

# 加载 nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 24

deploy_saas() {
  echo ""
  echo "--- 构建 SaaS (onemipham.com/saas/) ---"
  rm -rf dist-saas
  VITE_BASE=/saas/ npx vite build --outDir dist-saas
  echo "--- 部署到 $SERVER:$SAAS_PATH ---"
  rsync -avz --delete dist-saas/ "$SERVER:$SAAS_PATH"
  rm -rf dist-saas
  echo "✅ SaaS 部署完成"
}

deploy_intranet() {
  echo ""
  echo "--- 构建 Intranet (rismedronxin.com/intranet/) ---"
  rm -rf dist-intranet
  VITE_BASE=/intranet/ npx vite build --outDir dist-intranet
  echo "--- 部署到 $SERVER:$INTRANET_PATH ---"
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
curl -skL -o /dev/null -w "SaaS:      %{http_code} https://onemipham.com/saas/\n" "https://onemipham.com/saas/"
curl -skL -o /dev/null -w "Intranet:  %{http_code} https://rismedronxin.com/intranet/login\n" "https://rismedronxin.com/intranet/login"
echo "=== 完成 ==="
