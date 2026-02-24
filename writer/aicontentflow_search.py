#!/usr/bin/env python3
"""
Brave Search API 调用脚本
用于八段式工作流的信息来源增强
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime

class BraveSearchClient:
    """Brave Search API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: Brave API Key，如果为空则从环境变量 BRAVE_API_KEY 读取
        """
        self.api_key = api_key or os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise ValueError("请设置 BRAVE_API_KEY 环境变量或传入 api_key 参数")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
    
    def search(
        self,
        query: str,
        count: int = 10,
        search_lang: str = "zh-CN",
        country: str = "CN",
        safesearch: str = "moderate",
        freshness: Optional[str] = None,
        text_decorations: bool = False,
        spellcheck: bool = True
    ) -> Dict:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            count: 返回结果数量 (1-20)
            search_lang: 搜索语言 (zh-CN, en-US 等)
            country: 国家代码 (CN, US 等)
            safesearch: 安全搜索级别 (off, moderate, strict)
            freshness: 时效性过滤 (pd-最近24小时, pw-最近1周, pm-最近1月, py-最近1年)
            text_decorations: 是否在摘要中高亮关键词
            spellcheck: 是否启用拼写检查
            
        Returns:
            搜索结果字典
        """
        params = {
            "q": query,
            "count": count,
            "search_lang": search_lang,
            "country": country,
            "safesearch": safesearch,
            "text_decorations": text_decorations,
            "spellcheck": spellcheck
        }
        
        if freshness:
            params["freshness"] = freshness
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def format_results(self, results: Dict, output_format: str = "markdown") -> str:
        """
        格式化搜索结果
        
        Args:
            results: 搜索结果字典
            output_format: 输出格式 (markdown, json, text)
            
        Returns:
            格式化后的字符串
        """
        if "error" in results:
            return f"❌ 搜索失败: {results['error']}"
        
        if output_format == "json":
            return json.dumps(results, ensure_ascii=False, indent=2)
        
        # 提取核心数据
        query = results.get("query", {}).get("original", "")
        web_results = results.get("web", {}).get("results", [])
        news_results = results.get("news", {}).get("results", [])
        
        if output_format == "markdown":
            output = []
            output.append(f"# 🔍 搜索结果：{query}\n")
            output.append(f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.append(f"**结果数量**: {len(web_results)} 条网页 + {len(news_results)} 条新闻\n")
            output.append("---\n")
            
            # 网页结果
            if web_results:
                output.append("## 📄 网页结果\n")
                for idx, item in enumerate(web_results, 1):
                    title = item.get("title", "无标题")
                    url = item.get("url", "")
                    description = item.get("description", "无描述")
                    age = item.get("age", "")
                    
                    output.append(f"### {idx}. {title}\n")
                    output.append(f"**URL**: {url}\n")
                    if age:
                        output.append(f"**发布时间**: {age}\n")
                    output.append(f"**摘要**: {description}\n\n")
            
            # 新闻结果
            if news_results:
                output.append("## 📰 新闻结果\n")
                for idx, item in enumerate(news_results, 1):
                    title = item.get("title", "无标题")
                    url = item.get("url", "")
                    description = item.get("description", "无描述")
                    age = item.get("age", "")
                    
                    output.append(f"### {idx}. {title}\n")
                    output.append(f"**URL**: {url}\n")
                    if age:
                        output.append(f"**发布时间**: {age}\n")
                    output.append(f"**摘要**: {description}\n\n")
            
            return "".join(output)
        
        else:  # text
            output = []
            output.append(f"搜索关键词: {query}\n")
            output.append(f"结果数量: {len(web_results)} 条\n")
            output.append("=" * 50 + "\n")
            
            for idx, item in enumerate(web_results, 1):
                output.append(f"{idx}. {item.get('title', '无标题')}\n")
                output.append(f"   {item.get('url', '')}\n")
                output.append(f"   {item.get('description', '无描述')}\n\n")
            
            return "".join(output)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Brave Search API 调用工具")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-k", "--api-key", help="Brave API Key（可选，优先从环境变量读取）")
    parser.add_argument("-c", "--count", type=int, default=10, help="返回结果数量（默认10）")
    parser.add_argument("-l", "--lang", default="zh-CN", help="搜索语言（默认zh-CN）")
    parser.add_argument("-f", "--freshness", help="时效性（pd/pw/pm/py）")
    parser.add_argument("-o", "--output", choices=["markdown", "json", "text"], default="markdown", help="输出格式")
    parser.add_argument("--save", help="保存到文件路径")
    
    args = parser.parse_args()
    
    try:
        client = BraveSearchClient(api_key=args.api_key)
        results = client.search(
            query=args.query,
            count=args.count,
            search_lang=args.lang,
            freshness=args.freshness
        )
        
        formatted = client.format_results(results, output_format=args.output)
        
        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(formatted)
            print(f"✅ 结果已保存到: {args.save}")
        else:
            print(formatted)
            
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
