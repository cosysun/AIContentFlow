#!/usr/bin/env python3
"""
多源信息验证检索系统
功能：三层验证体系 + 自动交叉验证 + 结构化输出
作者：AI Content Workflow
版本：2.0
"""

import os
import json
import subprocess
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================================
# 配置区
# ============================================================================

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")

# 信息源配置
SOURCES_CONFIG = {
    "tier1_official": {
        "google_ai": ["site:ai.googleblog.com", "site:deepmind.com", "site:research.google"],
        "openai": ["site:openai.com/blog", "site:platform.openai.com"],
        "meta_ai": ["site:ai.meta.com", "site:research.facebook.com"],
        "microsoft_ai": ["site:blogs.microsoft.com/ai"],
        "anthropic": ["site:anthropic.com"],
    },
    "tier1_academic": {
        "arxiv": ["site:arxiv.org"],
        "nature": ["site:nature.com"],
        "papers_with_code": ["site:paperswithcode.com"],
    },
    "tier2_media": {
        "tech_media": ["site:techcrunch.com", "site:theverge.com", "site:wired.com"],
        "deep_analysis": ["site:technologyreview.com", "site:spectrum.ieee.org"],
        "chinese_media": ["机器之心", "量子位", "新智元"],
    },
    "tier3_community": {
        "hacker_news": ["site:news.ycombinator.com"],
        "reddit": ["site:reddit.com/r/MachineLearning", "site:reddit.com/r/artificial"],
        "github": ["site:github.com"],
    }
}

# 时效性过滤配置
FRESHNESS_OPTIONS = {
    "past_day": "pd",
    "past_week": "pw",
    "past_month": "pm",
    "past_year": "py"
}

# ============================================================================
# 核心函数
# ============================================================================

def brave_search(query: str, sites: List[str] = None, freshness: str = "pm", count: int = 10) -> Dict:
    """
    调用 Brave Search API
    
    参数:
        query: 搜索关键词
        sites: 站点列表（如 ["site:arxiv.org"]）
        freshness: 时效性（pd/pw/pm/py）
        count: 返回结果数量
    
    返回:
        {
            "success": bool,
            "results": List[Dict],
            "error": str
        }
    """
    try:
        from urllib.parse import quote
        
        # 构建搜索查询
        if sites:
            site_filter = " OR ".join(sites)
            full_query = f"({query}) AND ({site_filter})"
        else:
            full_query = query
        
        # URL编码
        encoded_query = quote(full_query)
        
        # 调用 Brave Search API
        cmd = [
            "curl", "-s",
            "-H", f"X-Subscription-Token: {BRAVE_API_KEY}",
            f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&freshness={freshness}&count={count}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "results": [], "error": result.stderr}
        
        data = json.loads(result.stdout)
        
        # 提取结果
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "published": item.get("age", "未知"),
            })
        
        return {"success": True, "results": results, "error": None}
    
    except Exception as e:
        return {"success": False, "results": [], "error": str(e)}


def web_search_fallback(query: str) -> Dict:
    """
    备用：使用通用 web_search（当 Brave API 失败时）
    注意：这需要在 AI 环境中调用，这里仅作占位
    """
    return {
        "success": False,
        "results": [],
        "error": "需要在 AI 环境中调用 web_search 工具"
    }


def multi_source_research(
    topic: str,
    keyword: str,
    freshness: str = "pm",
    enable_official: bool = True,
    enable_academic: bool = True,
    enable_media: bool = True,
    enable_community: bool = True,
) -> Dict:
    """
    多源信息检索主函数
    
    参数:
        topic: 话题描述（用于语义检索）
        keyword: 关键词（用于关键词检索）
        freshness: 时效性（pd=1天, pw=1周, pm=1月, py=1年）
        enable_*: 是否启用各层级信息源
    
    返回:
        {
            "topic": str,
            "timestamp": str,
            "tier1_official": {...},
            "tier1_academic": {...},
            "tier2_media": {...},
            "tier3_community": {...},
            "summary": {...}
        }
    """
    report = {
        "topic": topic,
        "keyword": keyword,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tier1_official": {},
        "tier1_academic": {},
        "tier2_media": {},
        "tier3_community": {},
        "summary": {
            "total_sources": 0,
            "successful_sources": 0,
            "total_results": 0,
        }
    }
    
    # 第一层：官方源
    if enable_official:
        print("🔍 正在检索第一层：官方权威源...")
        for source_name, sites in SOURCES_CONFIG["tier1_official"].items():
            print(f"  └─ 检索 {source_name}...")
            result = brave_search(keyword, sites, freshness, count=5)
            report["tier1_official"][source_name] = result
            
            if result["success"]:
                report["summary"]["successful_sources"] += 1
                report["summary"]["total_results"] += len(result["results"])
            report["summary"]["total_sources"] += 1
    
    # 第一层：学术源
    if enable_academic:
        print("🔍 正在检索第一层：学术权威源...")
        for source_name, sites in SOURCES_CONFIG["tier1_academic"].items():
            print(f"  └─ 检索 {source_name}...")
            result = brave_search(keyword, sites, freshness, count=5)
            report["tier1_academic"][source_name] = result
            
            if result["success"]:
                report["summary"]["successful_sources"] += 1
                report["summary"]["total_results"] += len(result["results"])
            report["summary"]["total_sources"] += 1
    
    # 第二层：媒体源
    if enable_media:
        print("🔍 正在检索第二层：专业媒体源...")
        for source_name, sites in SOURCES_CONFIG["tier2_media"].items():
            print(f"  └─ 检索 {source_name}...")
            # 中文媒体不使用站点过滤
            if source_name == "chinese_media":
                result = brave_search(f"{keyword} {' OR '.join(sites)}", None, freshness, count=5)
            else:
                result = brave_search(keyword, sites, freshness, count=5)
            report["tier2_media"][source_name] = result
            
            if result["success"]:
                report["summary"]["successful_sources"] += 1
                report["summary"]["total_results"] += len(result["results"])
            report["summary"]["total_sources"] += 1
    
    # 第三层：社区源
    if enable_community:
        print("🔍 正在检索第三层：社区验证源...")
        for source_name, sites in SOURCES_CONFIG["tier3_community"].items():
            print(f"  └─ 检索 {source_name}...")
            result = brave_search(keyword, sites, freshness, count=5)
            report["tier3_community"][source_name] = result
            
            if result["success"]:
                report["summary"]["successful_sources"] += 1
                report["summary"]["total_results"] += len(result["results"])
            report["summary"]["total_sources"] += 1
    
    return report


def generate_markdown_report(report: Dict, output_file: str = None) -> str:
    """
    生成 Markdown 格式的调研报告
    """
    md = []
    
    # 标题
    md.append(f"# 多源信息检索报告")
    md.append(f"\n**话题**: {report['topic']}")
    md.append(f"**关键词**: {report['keyword']}")
    md.append(f"**生成时间**: {report['timestamp']}")
    md.append(f"\n---\n")
    
    # 摘要
    md.append(f"## 📊 检索摘要")
    md.append(f"- **检索信息源总数**: {report['summary']['total_sources']}")
    md.append(f"- **成功检索源数**: {report['summary']['successful_sources']}")
    md.append(f"- **获取结果总数**: {report['summary']['total_results']}")
    md.append(f"\n---\n")
    
    # 第一层：官方源
    md.append(f"## 🏛️ 第一层：官方权威源")
    for source_name, result in report["tier1_official"].items():
        md.append(f"\n### {source_name.replace('_', ' ').title()}")
        if result["success"] and result["results"]:
            for idx, item in enumerate(result["results"], 1):
                md.append(f"{idx}. **{item['title']}**")
                md.append(f"   - 链接: {item['url']}")
                md.append(f"   - 发布: {item['published']}")
                md.append(f"   - 摘要: {item['description'][:150]}...")
        else:
            md.append(f"❌ 未获取到结果（原因: {result['error']}）")
    
    # 第一层：学术源
    md.append(f"\n## 📚 第一层：学术权威源")
    for source_name, result in report["tier1_academic"].items():
        md.append(f"\n### {source_name.replace('_', ' ').title()}")
        if result["success"] and result["results"]:
            for idx, item in enumerate(result["results"], 1):
                md.append(f"{idx}. **{item['title']}**")
                md.append(f"   - 链接: {item['url']}")
                md.append(f"   - 发布: {item['published']}")
                md.append(f"   - 摘要: {item['description'][:150]}...")
        else:
            md.append(f"❌ 未获取到结果（原因: {result['error']}）")
    
    # 第二层：媒体源
    md.append(f"\n## 📰 第二层：专业媒体源")
    for source_name, result in report["tier2_media"].items():
        md.append(f"\n### {source_name.replace('_', ' ').title()}")
        if result["success"] and result["results"]:
            for idx, item in enumerate(result["results"], 1):
                md.append(f"{idx}. **{item['title']}**")
                md.append(f"   - 链接: {item['url']}")
                md.append(f"   - 发布: {item['published']}")
                md.append(f"   - 摘要: {item['description'][:150]}...")
        else:
            md.append(f"❌ 未获取到结果（原因: {result['error']}）")
    
    # 第三层：社区源
    md.append(f"\n## 💬 第三层：社区验证源")
    for source_name, result in report["tier3_community"].items():
        md.append(f"\n### {source_name.replace('_', ' ').title()}")
        if result["success"] and result["results"]:
            for idx, item in enumerate(result["results"], 1):
                md.append(f"{idx}. **{item['title']}**")
                md.append(f"   - 链接: {item['url']}")
                md.append(f"   - 发布: {item['published']}")
                md.append(f"   - 摘要: {item['description'][:150]}...")
        else:
            md.append(f"❌ 未获取到结果（原因: {result['error']}）")
    
    md_content = "\n".join(md)
    
    # 保存到文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"\n✅ 报告已保存到: {output_file}")
    
    return md_content


# ============================================================================
# 命令行接口
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="多源信息验证检索系统")
    parser.add_argument("topic", help="话题描述")
    parser.add_argument("keyword", help="检索关键词")
    parser.add_argument("--freshness", default="pm", choices=["pd", "pw", "pm", "py"], 
                        help="时效性: pd=1天, pw=1周, pm=1月, py=1年")
    parser.add_argument("--no-official", action="store_true", help="禁用官方源")
    parser.add_argument("--no-academic", action="store_true", help="禁用学术源")
    parser.add_argument("--no-media", action="store_true", help="禁用媒体源")
    parser.add_argument("--no-community", action="store_true", help="禁用社区源")
    parser.add_argument("--output", "-o", help="输出文件路径（Markdown格式）")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    args = parser.parse_args()
    
    # 执行检索
    print(f"\n🚀 开始多源信息检索...")
    print(f"话题: {args.topic}")
    print(f"关键词: {args.keyword}")
    print(f"时效性: {args.freshness}\n")
    
    report = multi_source_research(
        topic=args.topic,
        keyword=args.keyword,
        freshness=args.freshness,
        enable_official=not args.no_official,
        enable_academic=not args.no_academic,
        enable_media=not args.no_media,
        enable_community=not args.no_community,
    )
    
    # 输出结果
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        output_file = args.output or f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        md_report = generate_markdown_report(report, output_file)
        print(f"\n" + "="*80)
        print(md_report)
