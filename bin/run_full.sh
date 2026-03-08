#!/bin/bash

# AIContentFlow - 完整流程脚本
# 用途：一键执行从监控到内容生成的完整流程

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AIContentFlow - 完整工作流${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 步骤1：运行监控
echo -e "${GREEN}━━━ 步骤 1/2: 热点监控 ━━━${NC}"
bash /data/workspace/AIContentFlow/run_monitor.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}[错误] 监控步骤失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 等待用户确认选题
echo -e "${BLUE}📋 请查看监控报告并选择主题${NC}"
echo ""
echo -e "${YELLOW}请输入要创作的主题名称（或直接按回车选择评分最高的）：${NC}"
read -r TOPIC

# 如果用户没有输入，从JSON中提取评分最高的主题
if [ -z "$TOPIC" ]; then
    echo -e "${YELLOW}[提示] 未输入主题，正在选择评分最高的主题...${NC}"
    
    # 简化版：提示用户必须输入
    echo -e "${RED}[错误] 请明确指定主题名称${NC}"
    echo ""
    echo -e "${YELLOW}示例：${NC}"
    echo "   bash run_full.sh"
    echo "   （然后输入主题名称）"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━ 步骤 2/2: 内容生成 ━━━${NC}"

# 步骤2：运行Writer
bash /data/workspace/AIContentFlow/run_writer.sh "$TOPIC"

echo ""
echo -e "${GREEN}✅ 完整流程已启动！${NC}"
echo -e "${YELLOW}💡 请在对话中继续与AI交互完成内容创作${NC}"