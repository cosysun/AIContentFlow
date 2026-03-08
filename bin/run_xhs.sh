#!/bin/bash

# AIContentFlow - 小红书完整流程
# 用途：从原始文章一键生成小红书正文 + 图片 Prompts + 上传 Notion
# 用法：bash run_xhs.sh <文章路径.md>
# 示例：bash run_xhs.sh /data/workspace/.draft/2026-03-08/龙虾之父访谈.md

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ARTICLE_PATH="$1"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AIContentFlow - 小红书完整流程${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 参数检查
if [ -z "$ARTICLE_PATH" ]; then
    echo -e "${RED}[错误] 请提供文章路径${NC}"
    echo ""
    echo -e "${YELLOW}用法：${NC}"
    echo "   bash run_xhs.sh <文章路径.md>"
    echo ""
    echo -e "${YELLOW}示例：${NC}"
    echo "   bash run_xhs.sh /data/workspace/.draft/2026-03-08/龙虾之父访谈.md"
    exit 1
fi

if [ ! -f "$ARTICLE_PATH" ]; then
    echo -e "${RED}[错误] 文件不存在：${ARTICLE_PATH}${NC}"
    exit 1
fi

ARTICLE_NAME=$(basename "$ARTICLE_PATH" .md)
DATE_STR=$(date +%Y-%m-%d)
OUTPUT_DIR="/data/workspace/AIContentFlow/outputs/archive/${DATE_STR}"
mkdir -p "$OUTPUT_DIR"

echo -e "${GREEN}📄 文章：${NC}${ARTICLE_NAME}"
echo -e "${GREEN}📁 输出目录：${NC}${OUTPUT_DIR}"
echo ""

# ─────────────────────────────────────────
# Step 1：生成小红书正文
# ─────────────────────────────────────────
echo -e "${GREEN}━━━ Step 1/3: 生成小红书正文 ━━━${NC}"
echo ""

python3 /data/workspace/AIContentFlow/tools/xhs_writer.py "$ARTICLE_PATH"

XHS_TEXT_FILE="${OUTPUT_DIR}/${ARTICLE_NAME}_小红书正文.md"

if [ ! -f "$XHS_TEXT_FILE" ]; then
    echo -e "${RED}[错误] 正文文件未生成：${XHS_TEXT_FILE}${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 正文已保存：${XHS_TEXT_FILE}${NC}"
echo ""

# ─────────────────────────────────────────
# Step 2：生成图片 Prompts
# ─────────────────────────────────────────
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}━━━ Step 2/3: 生成图片 Prompts ━━━${NC}"
echo ""

python3 /data/workspace/AIContentFlow/tools/xhs_image_pipeline.py "$ARTICLE_PATH"

PROMPTS_FILE="${OUTPUT_DIR}/${ARTICLE_NAME}_小红书图片prompts.md"

if [ ! -f "$PROMPTS_FILE" ]; then
    # 兼容旧命名格式
    PROMPTS_FILE=$(find "$OUTPUT_DIR" -name "*prompts*" | head -1)
fi

if [ -z "$PROMPTS_FILE" ] || [ ! -f "$PROMPTS_FILE" ]; then
    echo -e "${RED}[错误] Prompts 文件未生成${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Prompts 已保存：${PROMPTS_FILE}${NC}"
echo ""

# ─────────────────────────────────────────
# Step 3：上传 Notion 草稿箱
# ─────────────────────────────────────────
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}━━━ Step 3/3: 上传 Notion ━━━${NC}"
echo ""

python3 /data/workspace/AIContentFlow/publisher/notion_publisher.py --file "$PROMPTS_FILE"

NOTION_RESULT=$?

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ✅ 小红书流程完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📋 产出文件：${NC}"
echo "   正文：${XHS_TEXT_FILE}"
echo "   Prompts：${PROMPTS_FILE}"
echo ""
echo -e "${YELLOW}📌 接下来：${NC}"
echo "   1. 打开 Notion 草稿链接（见上方输出）"
echo "   2. 从图01开始，复制 Prompt 给 nano banana pro 出图"
echo "   3. 图01先出，图02-08 带 --ref 图01.png 保持风格统一"
echo "   4. 图片 + 小红书正文 → 发布 ✅"
echo ""
