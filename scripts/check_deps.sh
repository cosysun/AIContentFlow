#!/bin/bash
# AIContentFlow 依赖项检查脚本
# 用法：bash check_deps.sh [--workflow monitor|writer|publisher|all]

WORKFLOW="${1:-all}"
ENV_FILE="/data/workspace/AIContentFlow/.env"
PROJECT_DIR="/data/workspace/AIContentFlow"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ERRORS=()
WARNINGS=()

echo -e "${CYAN}===== AIContentFlow 依赖项检查 =====${NC}"
echo ""

# ─── 1. 检查 .env 文件 ───────────────────────────────────────────
echo -e "${CYAN}[1/4] 检查 .env 文件...${NC}"
if [ ! -f "$ENV_FILE" ]; then
  ERRORS+=("❌ 缺少 .env 文件：请将 .env.example 复制为 .env 并填入真实密钥")
  echo -e "  ${RED}✗ .env 文件不存在${NC}"
else
  echo -e "  ${GREEN}✓ .env 文件存在${NC}"
  source "$ENV_FILE" 2>/dev/null
fi

# ─── 2. 检查必需环境变量 ─────────────────────────────────────────
echo -e "${CYAN}[2/4] 检查环境变量...${NC}"

check_env() {
  local VAR_NAME="$1"
  local DESCRIPTION="$2"
  local WORKFLOW_TAG="$3"
  local GET_URL="$4"

  # 仅在匹配 workflow 时检查
  if [ "$WORKFLOW" != "all" ] && [ "$WORKFLOW" != "$WORKFLOW_TAG" ]; then
    return
  fi

  local VALUE="${!VAR_NAME}"
  if [ -z "$VALUE" ] || [[ "$VALUE" == *"your_"* ]]; then
    ERRORS+=("❌ 缺少 ${VAR_NAME}（${DESCRIPTION}）→ 获取地址：${GET_URL}")
    echo -e "  ${RED}✗ ${VAR_NAME} 未配置${NC}（${DESCRIPTION}）"
  else
    echo -e "  ${GREEN}✓ ${VAR_NAME}${NC}"
  fi
}

# 核心（所有工作流都需要）
check_env "BRAVE_API_KEY"    "Brave 搜索 API，用于热点监控和内容调研" "monitor" "https://brave.com/search/api/"

# 发布相关
check_env "NOTION_TOKEN"           "Notion 集成 Token，用于发布文章" "publisher" "https://www.notion.so/my-integrations"
check_env "NOTION_PARENT_PAGE_ID"  "Notion 父页面 ID，文章归档目标" "publisher" "Notion 页面 URL 中的 32 位 ID"
check_env "NOTION_DRAFTS_PAGE_ID"  "Notion 草稿箱页面 ID"           "publisher" "Notion 页面 URL 中的 32 位 ID"
check_env "WECHAT_APPID"           "微信公众号 AppID"                "publisher" "微信公众平台 → 开发 → 基本配置"
check_env "WECHAT_APPSECRET"       "微信公众号 AppSecret"            "publisher" "微信公众平台 → 开发 → 基本配置"

# ─── 3. 检查 Python 依赖包 ──────────────────────────────────────
echo -e "${CYAN}[3/4] 检查 Python 依赖包...${NC}"

check_pip() {
  local PKG="$1"
  local INSTALL_CMD="$2"
  if ! python3 -c "import $PKG" 2>/dev/null; then
    ERRORS+=("❌ 缺少 Python 包 '${PKG}'，请运行：${INSTALL_CMD}")
    echo -e "  ${RED}✗ ${PKG} 未安装${NC}"
  else
    echo -e "  ${GREEN}✓ ${PKG}${NC}"
  fi
}

check_pip "dotenv"   "pip install python-dotenv"
check_pip "requests" "pip install requests"
check_pip "notion_client" "pip install notion-client"

# ─── 4. 检查关键脚本文件 ────────────────────────────────────────
echo -e "${CYAN}[4/4] 检查关键脚本文件...${NC}"

check_file() {
  local FILE_PATH="$1"
  local DESCRIPTION="$2"
  if [ ! -f "$FILE_PATH" ]; then
    ERRORS+=("❌ 缺少文件：${FILE_PATH}（${DESCRIPTION}）")
    echo -e "  ${RED}✗ $(basename $FILE_PATH) 不存在${NC}（${DESCRIPTION}）"
  else
    echo -e "  ${GREEN}✓ $(basename $FILE_PATH)${NC}"
  fi
}

check_file "$PROJECT_DIR/monitor/aicontentflow_monitor.py" "热点监控脚本"
check_file "$PROJECT_DIR/writer/aicontentflow_search.py"   "内容检索脚本"
check_file "$PROJECT_DIR/publisher/notion_publisher.py"    "Notion 发布脚本"
check_file "$PROJECT_DIR/publisher/wechat_publisher.py"    "微信发布脚本"

# ─── 汇总结果 ────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}===== 检查结果汇总 =====${NC}"

if [ ${#ERRORS[@]} -eq 0 ]; then
  echo -e "${GREEN}✅ 所有依赖项检查通过，可以正常使用 AIContentFlow！${NC}"
  exit 0
else
  echo -e "${RED}⚠️  发现 ${#ERRORS[@]} 个问题，请按以下步骤修复：${NC}"
  echo ""
  for i in "${!ERRORS[@]}"; do
    echo -e "  $((i+1)). ${ERRORS[$i]}"
  done
  echo ""
  echo -e "${YELLOW}修复完成后，重新运行：bash $PROJECT_DIR/scripts/check_deps.sh${NC}"
  exit 1
fi
