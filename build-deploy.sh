#!/bin/bash
# ================================================================
# EGP-IMS 双版本构建脚本
# 中文版 → rismedronxin.com/intranet  (腾讯云轻量服务器)
# 英文版 → mipham.ai                    (国际独立服务器)
# ================================================================
set -e

FRONTEND_DIR="$(cd "$(dirname "$0")/frontend" && pwd)"

echo "========================================="
echo "  EGP-IMS Dual Deployment Build"
echo "========================================="

# ── 中文版（国内）──
echo ""
echo "[1/2] 构建中文版 → rismedronxin.com/intranet ..."
cd "$FRONTEND_DIR"
VITE_BASE=/intranet/ VITE_DEFAULT_LOCALE=zh-CN npm run build
mv dist dist-intranet
echo "  ✅ 中文版构建完成: $FRONTEND_DIR/dist-intranet"

# ── 英文版（国际）──
echo ""
echo "[2/2] 构建英文版 → mipham.ai ..."
VITE_BASE=/ VITE_DEFAULT_LOCALE=en-US npm run build
mv dist dist-saas
echo "  ✅ 英文版构建完成: $FRONTEND_DIR/dist-saas"

echo ""
echo "========================================="
echo "  Build Complete"
echo "========================================="
echo ""
echo "  中文版: $FRONTEND_DIR/dist-intranet/"
echo "    → 部署到: rismedronxin.com/intranet"
echo ""
echo "  英文版: $FRONTEND_DIR/dist-saas/"
echo "    → 部署到: mipham.ai"
echo ""
echo "  Nginx 配置:"
echo "    中文: deploy/intranet-nginx.conf"
echo "    英文: deploy/saas-nginx.conf"
