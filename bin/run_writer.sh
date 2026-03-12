#!/bin/bash

# AIContentFlow - 内容创作启动脚本
# 用途：根据选定主题保存选题，输出创作上下文，供 AI 工作流使用
# 用法：bash bin/run_writer.sh "主题名称" [article_type]
#   article_type 可选：科普|工具|编程|创业（默认自动判断）

set -e

# ── 颜色 ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TOPIC="$1"
ARTICLE_TYPE="${2:-}"
PROJECT_DIR="/data/workspace/AIContentFlow"
DRAFT_BASE="/data/workspace/.draft"
TODAY=$(date +%Y-%m-%d)
DRAFT_DIR="${DRAFT_BASE}/${TODAY}"
TOPIC_FILE="/data/workspace/.daily_topic_choice.txt"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AIContentFlow - 内容创作系统 v2.0${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── 检查主题参数 ───────────────────────────────────────────────────
if [ -z "$TOPIC" ]; then
    # 尝试从监控报告中读取第一条推荐选题
    REPORT="${PROJECT_DIR}/monitor/topic_monitor_report.md"
    if [ -f "$REPORT" ]; then
        echo -e "${YELLOW}[提示] 未指定主题，尝试从监控报告中读取推荐选题...${NC}"
        # 提取第一个推荐标题（格式：### 1. 标题 或 **标题**）
        TOPIC=$(grep -m1 -oP '(?<=\*\*)[^\*]+(?=\*\*)' "$REPORT" 2>/dev/null | head -1)
        if [ -z "$TOPIC" ]; then
            echo -e "${RED}[错误] 无法自动提取选题，请手动指定主题${NC}"
            echo ""
            echo -e "${YELLOW}用法：${NC}"
            echo "   bash bin/run_writer.sh \"主题名称\""
            echo "   bash bin/run_writer.sh \"主题名称\" 工具"
            echo ""
            echo -e "${YELLOW}示例：${NC}"
            echo "   bash bin/run_writer.sh \"Claude 3.5新功能深度解析\" 科普"
            echo "   bash bin/run_writer.sh \"用 Cursor 构建全栈应用\" 编程"
            exit 1
        fi
        echo -e "${GREEN}[自动选题] ${TOPIC}${NC}"
    else
        echo -e "${RED}[错误] 请先运行热点监控：bash bin/run_monitor.sh${NC}"
        echo ""
        echo -e "${YELLOW}或直接指定主题：${NC}"
        echo "   bash bin/run_writer.sh \"主题名称\""
        exit 1
    fi
fi

# ── 判断文章类型和字数 ─────────────────────────────────────────────
if [ -z "$ARTICLE_TYPE" ]; then
    # 根据关键词自动判断
    if echo "$TOPIC" | grep -qiE "教程|实战|代码|开发|工程|编程|python|javascript|rust|go语言|架构"; then
        ARTICLE_TYPE="编程"
    elif echo "$TOPIC" | grep -qiE "工具|插件|扩展|框架|库|SDK|API|平台|产品"; then
        ARTICLE_TYPE="工具"
    elif echo "$TOPIC" | grep -qiE "创业|商业|融资|市场|增长|出海|变现|赛道"; then
        ARTICLE_TYPE="创业"
    else
        ARTICLE_TYPE="科普"
    fi
fi

case "$ARTICLE_TYPE" in
    科普) TARGET_WORDS="3000-5000" ;;
    工具) TARGET_WORDS="4000-6000" ;;
    编程) TARGET_WORDS="6000-8000" ;;
    创业) TARGET_WORDS="8000-10000" ;;
    *) TARGET_WORDS="3000-5000"; ARTICLE_TYPE="科普" ;;
esac

# ── 创建草稿目录 ───────────────────────────────────────────────────
echo -e "${GREEN}[1/4] 创建草稿目录...${NC}"
mkdir -p "$DRAFT_DIR"
echo -e "  ${GREEN}✓ ${DRAFT_DIR}${NC}"

# ── 保存选题 ──────────────────────────────────────────────────────
echo -e "${GREEN}[2/4] 保存选题...${NC}"
echo "$TOPIC" > "$TOPIC_FILE"
echo -e "  ${GREEN}✓ 选题已保存到 ${TOPIC_FILE}${NC}"

# ── 生成 context.json ─────────────────────────────────────────────
echo -e "${GREEN}[3/4] 初始化进度上下文...${NC}"
CONTEXT_FILE="${DRAFT_DIR}/context.json"
cat > "$CONTEXT_FILE" << EOF
{
  "topic": "${TOPIC}",
  "selected_title": "",
  "current_stage": 1,
  "completed_stages": [],
  "article_type": "${ARTICLE_TYPE}",
  "target_words": "${TARGET_WORDS}",
  "draft_dir": "${DRAFT_DIR}",
  "last_updated": "$(date -Iseconds)"
}
EOF
echo -e "  ${GREEN}✓ context.json 已创建${NC}"

# ── 输出创作摘要 ──────────────────────────────────────────────────
echo -e "${GREEN}[4/4] 创作配置就绪${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📝 创作任务摘要${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  主题：${YELLOW}${TOPIC}${NC}"
echo -e "  类型：${YELLOW}${ARTICLE_TYPE}类${NC}"
echo -e "  字数：${YELLOW}${TARGET_WORDS} 字${NC}"
echo -e "  草稿：${YELLOW}${DRAFT_DIR}/${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📋 十段式写作工作流${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  阶段1：确认选题和创作目标"
echo "  阶段2：深度调研（≥15 个信息源）"
echo "  阶段3：内容创作（${TARGET_WORDS} 字）"
echo "  阶段4：第一遍审校 - 事实核查"
echo "  阶段5：第二遍审校 - 降AI味"
echo "  阶段6：第三遍审校 - 排版润色"
echo "  阶段7：标题创作（20 个方案）"
echo "  阶段8：最终审阅与暂存"
echo "  阶段9：全方位质检（十维度评分）"
echo "  阶段10：发布推广计划"
echo ""
echo -e "${YELLOW}⚠️  预计耗时：20-40 分钟${NC}"
echo ""
echo -e "${GREEN}✅ 准备就绪！AI 将自动启动十段式写作工作流。${NC}"
echo ""
echo -e "  草稿保存路径：${YELLOW}${DRAFT_DIR}/${NC}"
echo "  context.json：已初始化（阶段1待开始）"
echo ""
