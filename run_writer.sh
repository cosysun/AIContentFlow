#!/bin/bash

# AIContentFlow - 内容生成脚本
# 用途：根据选定主题生成专业内容

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

TOPIC="$1"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AIContentFlow - 内容生成系统${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 如果没有提供主题参数，尝试从报告中读取
if [ -z "$TOPIC" ]; then
    echo -e "${YELLOW}[提示] 未指定主题，将从监控报告中选择评分最高的主题${NC}"
    
    # 检查报告是否存在
    if [ ! -f "/data/workspace/AIContentFlow/outputs/topic_monitor_report.json" ]; then
        echo -e "${RED}[错误] 未找到监控报告，请先运行: bash run_monitor.sh${NC}"
        exit 1
    fi
    
    # 从JSON中提取评分最高的主题（这里需要jq工具或Python脚本）
    # 简化版：直接提示用户
    echo -e "${RED}[错误] 请指定主题名称${NC}"
    echo ""
    echo -e "${YELLOW}用法：${NC}"
    echo "   bash run_writer.sh \"主题名称\""
    echo ""
    echo -e "${YELLOW}示例：${NC}"
    echo "   bash run_writer.sh \"Claude 3.5新功能深度解析\""
    exit 1
fi

echo -e "${GREEN}[1/9] 确认选题：${NC}${TOPIC}"
echo ""

# 保存选题到临时文件
echo "$TOPIC" > /data/workspace/.daily_topic_choice.txt
echo -e "${GREEN}[2/9] 选题已保存${NC}"
echo ""

# 调用AI执行完整创作流程
echo -e "${GREEN}[3/9] 启动八段式创作工作流...${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📝 创作流程说明：${NC}"
echo "   阶段1: 确认选题和创作目标"
echo "   阶段2: 深度调研（15+信息源）"
echo "   阶段3: 内容创作（3000-10000字）"
echo "   阶段4: 三遍审校（事实核查+降AI味+排版润色）"
echo "   阶段5: 拟定20个标题方案"
echo "   阶段6: 最终审阅"
echo "   阶段7: 暂存到临时目录"
echo "   阶段8: 生成发布推广计划"
echo "   阶段9: 发布前确认"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${RED}⚠️  请注意：创作过程需要约15-30分钟${NC}"
echo -e "${RED}⚠️  请在对话中向AI发送以下消息：${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "请执行内容创作任务，主题为：${TOPIC}"
echo ""
echo "使用八段式专业写作工作流完整执行："
echo "- 阶段1：确认选题和创作目标"
echo "- 阶段2：深度调研（15+信息源）"
echo "- 阶段3：内容创作（根据内容线字数：科普3000-5000/工具4000-6000/编程6000-8000/创业8000-10000字）"
echo "- 阶段4：三遍审校（事实核查+降AI味+排版润色）"
echo "- 阶段5：拟定20个标题方案"
echo "- 阶段6：最终审阅"
echo "- 阶段7：暂存到临时目录 /data/workspace/.draft/$(date +%Y-%m-%d)/"
echo "- 阶段8：生成发布推广计划"
echo ""
echo "完成后使用notify工具通知我，标题为\"📝 内容已完成 - 请确认发布\"。"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}💡 提示：请将上述消息复制发送给AI助手${NC}"