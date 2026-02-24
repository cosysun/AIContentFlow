#!/bin/bash

# AIContentFlow - 热点监控脚本
# 用途：一键运行热点监控，生成选题报告

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AIContentFlow - 热点监控系统${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[警告] 未找到Python3环境${NC}"
    exit 1
fi

# 运行监控脚本
echo -e "${GREEN}[1/3] 正在运行热点监控...${NC}"
cd /data/workspace/AIContentFlow/monitor
python3 aicontentflow_monitor.py

# 检查输出文件
if [ -f "/data/workspace/AIContentFlow/outputs/topic_monitor_report.md" ]; then
    echo -e "${GREEN}[2/3] 报告生成成功！${NC}"
    echo ""
    echo -e "${BLUE}📊 报告位置：${NC}"
    echo "   /data/workspace/AIContentFlow/outputs/topic_monitor_report.md"
    echo ""
    
    # 显示报告预览（前30行）
    echo -e "${GREEN}[3/3] 报告预览：${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    head -n 30 /data/workspace/AIContentFlow/outputs/topic_monitor_report.md
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 下一步提示
    echo -e "${YELLOW}📝 下一步操作：${NC}"
    echo "   1. 查看完整报告: cat /data/workspace/AIContentFlow/outputs/topic_monitor_report.md"
    echo "   2. 确认选题后运行: bash /data/workspace/AIContentFlow/run_writer.sh [主题名称]"
    echo "   3. 或运行完整流程: bash /data/workspace/AIContentFlow/run_full.sh"
    echo ""
else
    echo -e "${YELLOW}[错误] 报告生成失败，请检查日志${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 监控完成！${NC}"