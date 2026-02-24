#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题评分系统 - Topic Scorer
用途：自动评估候选主题在四大内容线的得分，并给出执行建议

使用方法：
    python topic_scorer.py "候选主题名称"
    python topic_scorer.py "候选主题名称" --detailed  # 详细输出
    python topic_scorer.py --batch topics.txt  # 批量评分
"""

import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple

# ============================================
# 评分标准配置
# ============================================

# AI科普评分标准
KEPU_CRITERIA = {
    "热度": {"weight": 7, "description": "7天内搜索量、社交媒体讨论度"},
    "理解门槛": {"weight": 6, "description": "能否用小学生听得懂的话解释"},
    "视觉化潜力": {"weight": 5, "description": "能否用图表/流程图/对比表呈现"},
    "传播潜力": {"weight": 4, "description": "是否有'哇！'的惊叹点"},
    "长尾价值": {"weight": 3, "description": "3个月后是否还有人搜"}
}
KEPU_THRESHOLD = {"high": 18, "medium": 15}

# AI工具评分标准
TOOL_CRITERIA = {
    "需求强度": {"weight": 8, "description": "目标用户痛点有多痛"},
    "可验证性": {"weight": 7, "description": "能否通过实测获得客观数据"},
    "变现潜力": {"weight": 5, "description": "是否有联盟计划/付费版"},
    "竞品对比": {"weight": 3, "description": "市场上有几个可对比的竞品"},
    "使用门槛": {"weight": 2, "description": "普通用户能否10分钟上手"}
}
TOOL_THRESHOLD = {"high": 20, "medium": 16}

# AI编程评分标准
CODING_CRITERIA = {
    "技术深度": {"weight": 8, "description": "是否涉及架构设计/算法优化"},
    "实战价值": {"weight": 7, "description": "能否直接用于生产环境"},
    "代码完整性": {"weight": 5, "description": "是否有完整可运行的代码"},
    "前沿性": {"weight": 3, "description": "是否使用最新技术/框架"},
    "差异化": {"weight": 2, "description": "市面上是否有大量类似教程"}
}
CODING_THRESHOLD = {"high": 20, "medium": 17}

# AI出海创业评分标准
STARTUP_CRITERIA = {
    "商业价值": {"weight": 9, "description": "是否能指导实际商业决策"},
    "数据充分性": {"weight": 8, "description": "是否有15+独立信息源"},
    "全球视野": {"weight": 4, "description": "是否覆盖中美欧等多个市场"},
    "时效性": {"weight": 3, "description": "是否是近30天内的新动态"},
    "争议性": {"weight": 1, "description": "是否有不同观点碰撞"}
}
STARTUP_THRESHOLD = {"high": 22, "medium": 19}

# 内容线配置
CONTENT_LINES = {
    "AI科普": {
        "criteria": KEPU_CRITERIA,
        "threshold": KEPU_THRESHOLD,
        "total": 25,
        "color": "🔵"
    },
    "AI工具": {
        "criteria": TOOL_CRITERIA,
        "threshold": TOOL_THRESHOLD,
        "total": 25,
        "color": "🟢"
    },
    "AI编程": {
        "criteria": CODING_CRITERIA,
        "threshold": CODING_THRESHOLD,
        "total": 25,
        "color": "🟡"
    },
    "AI出海创业": {
        "criteria": STARTUP_CRITERIA,
        "threshold": STARTUP_THRESHOLD,
        "total": 25,
        "color": "🔴"
    }
}

# ============================================
# 评分引擎
# ============================================

class TopicScorer:
    """主题评分器"""
    
    def __init__(self, topic: str):
        self.topic = topic
        self.scores = {}
        
    def score_topic(self) -> Dict:
        """对主题进行评分"""
        print(f"\n{'='*60}")
        print(f"📝 正在评估主题：{self.topic}")
        print(f"{'='*60}\n")
        
        results = {}
        
        for line_name, line_config in CONTENT_LINES.items():
            print(f"\n{line_config['color']} 【{line_name}】评分中...")
            line_score = self._score_content_line(line_name, line_config)
            results[line_name] = line_score
            
        return results
    
    def _score_content_line(self, line_name: str, line_config: Dict) -> Dict:
        """对单个内容线评分"""
        criteria = line_config["criteria"]
        scores = {}
        total_score = 0
        
        for criterion_name, criterion_config in criteria.items():
            max_score = criterion_config["weight"]
            description = criterion_config["description"]
            
            # 交互式打分
            while True:
                try:
                    prompt = f"  {criterion_name}（{description}）[0-{max_score}]: "
                    score = int(input(prompt))
                    if 0 <= score <= max_score:
                        scores[criterion_name] = score
                        total_score += score
                        break
                    else:
                        print(f"    ❌ 请输入0-{max_score}之间的整数")
                except ValueError:
                    print(f"    ❌ 请输入有效的数字")
                except KeyboardInterrupt:
                    print("\n\n⚠️  评分已取消")
                    sys.exit(0)
        
        # 判断是否达标
        threshold = line_config["threshold"]
        if total_score >= threshold["high"]:
            status = "✅推荐"
            priority = "high"
        elif total_score >= threshold["medium"]:
            status = "⚠️ 观察"
            priority = "medium"
        else:
            status = "❌不推荐"
            priority = "low"
        
        return {
            "scores": scores,
            "total": total_score,
            "max": line_config["total"],
            "status": status,
            "priority": priority,
            "threshold": threshold
        }
    
    def generate_report(self, results: Dict) -> str:
        """生成评分报告"""
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"📊 主题评分报告")
        report.append(f"{'='*60}")
        report.append(f"主题：{self.topic}")
        report.append(f"评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"")
        
        # 各内容线详细得分
        for line_name, line_result in results.items():
            color = CONTENT_LINES[line_name]["color"]
            report.append(f"\n{color} 【{line_name}】得分：{line_result['total']}/{line_result['max']} {line_result['status']}")
            for criterion, score in line_result['scores'].items():
                max_score = CONTENT_LINES[line_name]['criteria'][criterion]['weight']
                bar = '█' * score + '░' * (max_score - score)
                report.append(f"  {criterion}: {score}/{max_score} {bar}")
        
        # 执行建议
        report.append(f"\n{'='*60}")
        report.append(f"💡 执行建议")
        report.append(f"{'='*60}")
        
        high_priority = [name for name, result in results.items() if result['priority'] == 'high']
        medium_priority = [name for name, result in results.items() if result['priority'] == 'medium']
        low_priority = [name for name, result in results.items() if result['priority'] == 'low']
        
        if len(high_priority) >= 3:
            report.append(f"\n✅ 建议：四维度展开（多个内容线得分达标）")
            report.append(f"\n推荐排期：")
            schedule = {
                "AI科普": "Day 1",
                "AI工具": "Day 3",
                "AI编程": "Day 7",
                "AI出海创业": "Day 14"
            }
            for line in high_priority:
                if line in schedule:
                    report.append(f"  {schedule[line]}: {line}版")
        
        elif len(high_priority) >= 1:
            report.append(f"\n✅ 建议：聚焦以下内容线")
            for line in high_priority:
                report.append(f"  - {line}（得分：{results[line]['total']}/25）")
        
        elif len(medium_priority) >= 1:
            report.append(f"\n⚠️  建议：观察热度变化，或考虑以下内容线")
            for line in medium_priority:
                report.append(f"  - {line}（得分：{results[line]['total']}/25）")
        
        else:
            report.append(f"\n❌ 建议：放弃该主题，或重新包装角度")
            report.append(f"\n💡 优化方向：")
            # 找出最接近达标的内容线
            closest_line = max(results.items(), key=lambda x: x[1]['total'])
            report.append(f"  - {closest_line[0]}最接近达标（{closest_line[1]['total']}/25）")
            report.append(f"  - 建议从该角度重新包装主题")
        
        # 信息源建议
        report.append(f"\n{'='*60}")
        report.append(f"📚 调研建议")
        report.append(f"{'='*60}")
        
        if high_priority:
            source_requirements = {
                "AI科普": "5-8个信息源",
                "AI工具": "8-10个信息源（必须包含实测数据）",
                "AI编程": "10-12个信息源（必须包含完整代码）",
                "AI出海创业": "15+个信息源（必须包含财报/分析师报告）"
            }
            report.append(f"\n信息源数量要求：")
            for line in high_priority:
                report.append(f"  - {line}: {source_requirements.get(line, '未知')}")
        
        report.append(f"\n{'='*60}")
        
        return "\n".join(report)
    
    def save_report(self, results: Dict, output_file: str = None):
        """保存评分报告"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = "".join(c for c in self.topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            output_file = f"topic_score_{safe_topic}_{timestamp}.json"
        
        data = {
            "topic": self.topic,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "high_priority": [name for name, result in results.items() if result['priority'] == 'high'],
                "medium_priority": [name for name, result in results.items() if result['priority'] == 'medium'],
                "low_priority": [name for name, result in results.items() if result['priority'] == 'low']
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 评分数据已保存：{output_file}")
        
        return output_file

# ============================================
# 快速评分模式（预设值）
# ============================================

def quick_score(topic: str, preset: str = "example") -> Dict:
    """快速评分（使用预设值，用于演示）"""
    
    presets = {
        "gemini_review": {
            "AI科普": {"热度": 7, "理解门槛": 6, "视觉化潜力": 5, "传播潜力": 4, "长尾价值": 0},
            "AI工具": {"需求强度": 8, "可验证性": 7, "变现潜力": 5, "竞品对比": 3, "使用门槛": 0},
            "AI编程": {"技术深度": 8, "实战价值": 6, "代码完整性": 5, "前沿性": 3, "差异化": 0},
            "AI出海创业": {"商业价值": 9, "数据充分性": 8, "全球视野": 4, "时效性": 3, "争议性": 0}
        },
        "niche_tool": {
            "AI科普": {"热度": 3, "理解门槛": 5, "视觉化潜力": 2, "传播潜力": 2, "长尾价值": 0},
            "AI工具": {"需求强度": 4, "可验证性": 3, "变现潜力": 2, "竞品对比": 2, "使用门槛": 2},
            "AI编程": {"技术深度": 4, "实战价值": 3, "代码完整性": 3, "前沿性": 1, "差异化": 2},
            "AI出海创业": {"商业价值": 2, "数据充分性": 3, "全球视野": 0, "时效性": 2, "争议性": 1}
        }
    }
    
    if preset not in presets:
        print(f"❌ 未知的预设：{preset}")
        return None
    
    preset_scores = presets[preset]
    results = {}
    
    for line_name, line_config in CONTENT_LINES.items():
        if line_name not in preset_scores:
            continue
        
        scores = preset_scores[line_name]
        total_score = sum(scores.values())
        
        threshold = line_config["threshold"]
        if total_score >= threshold["high"]:
            status = "✅推荐"
            priority = "high"
        elif total_score >= threshold["medium"]:
            status = "⚠️ 观察"
            priority = "medium"
        else:
            status = "❌不推荐"
            priority = "low"
        
        results[line_name] = {
            "scores": scores,
            "total": total_score,
            "max": line_config["total"],
            "status": status,
            "priority": priority,
            "threshold": threshold
        }
    
    return results

# ============================================
# 主程序
# ============================================

def main():
    parser = argparse.ArgumentParser(description='主题评分系统')
    parser.add_argument('topic', nargs='?', help='候选主题名称')
    parser.add_argument('--quick', choices=['gemini_review', 'niche_tool'], help='快速评分（使用预设值）')
    parser.add_argument('--batch', help='批量评分（从文件读取主题列表）')
    parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 批量评分模式
    if args.batch:
        print(f"📂 批量评分模式（暂未实现）")
        print(f"📄 读取文件：{args.batch}")
        return
    
    # 快速评分模式
    if args.quick:
        if not args.topic:
            print("❌ 请提供主题名称")
            return
        
        print(f"\n⚡ 快速评分模式（使用预设：{args.quick}）")
        results = quick_score(args.topic, args.quick)
        
        if results:
            scorer = TopicScorer(args.topic)
            report = scorer.generate_report(results)
            print(report)
            
            if args.output:
                scorer.save_report(results, args.output)
        
        return
    
    # 交互式评分模式
    if not args.topic:
        print("❌ 请提供主题名称")
        print(f"\n使用方法：")
        print(f"  python topic_scorer.py \"主题名称\"")
        print(f"  python topic_scorer.py \"主题名称\" --quick gemini_review  # 快速演示")
        return
    
    scorer = TopicScorer(args.topic)
    results = scorer.score_topic()
    report = scorer.generate_report(results)
    print(report)
    
    # 保存评分数据
    scorer.save_report(results, args.output)

if __name__ == "__main__":
    main()
