# AI热点监控系统

> 版本：v1.0  
> 更新时间：2026-02-21  
> 用途：自动追踪AI行业动态，每日推送候选主题

---

## 📋 目录

1. [系统架构](#系统架构)
2. [监控源配置](#监控源配置)
3. [自动化脚本](#自动化脚本)
4. [使用指南](#使用指南)
5. [输出示例](#输出示例)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   数据采集层                          │
├─────────────────────────────────────────────────────┤
│  Google News API  │  HackerNews  │  Reddit API      │
│  Twitter API      │  ProductHunt │  arXiv RSS       │
│  TechCrunch RSS   │  Brave Search│  GitHub Trending │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                   数据处理层                          │
├─────────────────────────────────────────────────────┤
│  • 关键词过滤                                         │
│  • 热度计算（讨论量、搜索量、传播速度）                │
│  • 去重                                              │
│  • 分类（AI科普/AI工具/AI编程/AI出海创业）            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                   评分层                             │
├─────────────────────────────────────────────────────┤
│  调用 topic_scorer.py                                │
│  • 自动初步评分                                       │
│  • 推荐优先级排序                                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                   输出层                             │
├─────────────────────────────────────────────────────┤
│  • Markdown报告                                      │
│  • JSON数据                                          │
│  • 邮件/企业微信推送（可选）                          │
└─────────────────────────────────────────────────────┘
```

---

## 📡 监控源配置

### 1. Google News（需API Key）

**用途**：获取主流媒体报道  
**更新频率**：实时  
**关键词**：
```
AI, Artificial Intelligence, Machine Learning, 
Deep Learning, GPT, Gemini, Claude, LLM, 
Generative AI, AI Tools, AI Coding
```

**API配置**：
```python
GOOGLE_NEWS_CONFIG = {
    "api_key": "YOUR_API_KEY",  # 从 https://newsapi.org 获取
    "keywords": ["AI", "Artificial Intelligence", "Machine Learning"],
    "language": "en",
    "sortBy": "publishedAt",
    "pageSize": 50
}
```

---

### 2. HackerNews（无需API Key）

**用途**：开发者社区热议话题  
**更新频率**：每小时  
**抓取内容**：Top Stories前30条

**API端点**：
```
https://hacker-news.firebaseio.com/v0/topstories.json
```

**代码示例**：
```python
import requests

def fetch_hackernews_top():
    """获取HackerNews热门话题"""
    # 获取Top Stories ID列表
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    story_ids = requests.get(url).json()[:30]
    
    stories = []
    for story_id in story_ids:
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        story = requests.get(story_url).json()
        
        # 过滤AI相关
        if story and 'title' in story:
            title = story['title'].lower()
            if any(kw in title for kw in ['ai', 'gpt', 'llm', 'machine learning']):
                stories.append({
                    "title": story['title'],
                    "url": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                    "score": story.get('score', 0),
                    "comments": story.get('descendants', 0)
                })
    
    return stories
```

---

### 3. Reddit（需API认证）

**用途**：技术社区深度讨论  
**监控子版块**：
- r/MachineLearning
- r/artificial
- r/ArtificialIntelligence
- r/LocalLLaMA
- r/OpenAI

**API配置**：
```python
REDDIT_CONFIG = {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "user_agent": "AI Topic Monitor v1.0"
}

# 需要在 https://www.reddit.com/prefs/apps 创建应用
```

---

### 4. Twitter/X（需API v2认证）

**用途**：实时热点追踪  
**监控账号**（AI KOL）：
```
@sama (Sam Altman - OpenAI)
@drfeifei (Fei-Fei Li - Stanford)
@AndrewYNg (Andrew Ng)
@karpathy (Andrej Karpathy)
@emollick (Ethan Mollick - AI教育)
@ylecun (Yann LeCun - Meta)
@GaryMarcus (Gary Marcus - AI批评者)
```

**API配置**：
```python
TWITTER_CONFIG = {
    "bearer_token": "YOUR_BEARER_TOKEN",
    "tracked_users": [
        "sama", "drfeifei", "AndrewYNg", "karpathy",
        "emollick", "ylecun", "GaryMarcus"
    ],
    "keywords": ["AI", "GPT", "LLM", "Gemini"]
}
```

---

### 5. ProductHunt（无需API Key）

**用途**：新AI工具发现  
**抓取内容**：每日Top 10 AI工具

**RSS订阅**：
```
https://www.producthunt.com/topics/artificial-intelligence.rss
```

**代码示例**：
```python
import feedparser

def fetch_producthunt_ai_tools():
    """获取ProductHunt AI工具"""
    feed = feedparser.parse("https://www.producthunt.com/topics/artificial-intelligence.rss")
    
    tools = []
    for entry in feed.entries[:10]:
        tools.append({
            "name": entry.title,
            "url": entry.link,
            "description": entry.summary,
            "published": entry.published
        })
    
    return tools
```

---

### 6. arXiv（无需API Key）

**用途**：学术前沿论文  
**监控分类**：
- cs.AI（人工智能）
- cs.CL（计算语言学）
- cs.CV（计算机视觉）
- cs.LG（机器学习）

**RSS订阅**：
```
http://export.arxiv.org/rss/cs.AI
http://export.arxiv.org/rss/cs.CL
http://export.arxiv.org/rss/cs.LG
```

---

### 7. TechCrunch（无需API Key）

**用途**：科技新闻报道  
**RSS订阅**：
```
https://techcrunch.com/category/artificial-intelligence/feed/
```

---

### 8. Brave Search API（推荐，替代Google）

**用途**：搜索趋势分析  
**优势**：免费额度更高，无需翻墙

**API配置**：
```python
BRAVE_SEARCH_CONFIG = {
    "api_key": "YOUR_BRAVE_API_KEY",  # 从 https://brave.com/search/api/ 获取
    "endpoint": "https://api.search.brave.com/res/v1/web/search",
    "queries": [
        "AI news today",
        "new AI tools",
        "AI startup funding",
        "latest AI research"
    ]
}
```

---

### 9. GitHub Trending（无需API Key）

**用途**：热门AI项目  
**监控语言**：Python, JavaScript, TypeScript

**抓取URL**：
```
https://github.com/trending/python?since=daily
https://github.com/trending/jupyter-notebook?since=daily
```

---

## 🤖 自动化脚本

### 主脚本：ai_monitor.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI热点监控系统
每日自动抓取AI行业动态，生成候选主题报告

运行方式：
    python ai_monitor.py              # 运行一次
    python ai_monitor.py --daemon     # 后台运行（每4小时）
    python ai_monitor.py --test       # 测试模式
"""

import requests
import feedparser
import json
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict
import time

# ============================================
# 配置
# ============================================

# Brave Search API配置（推荐）
BRAVE_API_KEY = "YOUR_API_KEY"  # 从 https://brave.com/search/api/ 获取

# 可选：其他API配置
REDDIT_CLIENT_ID = ""
REDDIT_CLIENT_SECRET = ""
TWITTER_BEARER_TOKEN = ""

# 关键词配置
AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "deep learning",
    "GPT", "Gemini", "Claude", "LLM", "large language model",
    "generative AI", "AI tools", "AI coding", "AI startup"
]

# 热度阈值
TRENDING_THRESHOLD = {
    "high": 5000,    # 24小时内讨论量 > 5000
    "medium": 1000,  # 1000-5000
    "low": 100       # 100-1000
}

# ============================================
# 数据采集模块
# ============================================

def fetch_hackernews():
    """抓取HackerNews热门话题"""
    print("📰 正在抓取 HackerNews...")
    
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        story_ids = requests.get(url, timeout=10).json()[:30]
        
        stories = []
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story = requests.get(story_url, timeout=10).json()
            
            if story and 'title' in story:
                title = story['title'].lower()
                if any(kw.lower() in title for kw in AI_KEYWORDS):
                    stories.append({
                        "source": "HackerNews",
                        "title": story['title'],
                        "url": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": story.get('score', 0),
                        "comments": story.get('descendants', 0),
                        "timestamp": datetime.now().isoformat()
                    })
        
        print(f"  ✅ 找到 {len(stories)} 条AI相关话题")
        return stories
    
    except Exception as e:
        print(f"  ❌ 抓取失败：{e}")
        return []

def fetch_brave_search():
    """使用Brave Search API搜索AI热点"""
    print("🔍 正在使用 Brave Search...")
    
    if not BRAVE_API_KEY or BRAVE_API_KEY == "YOUR_API_KEY":
        print("  ⚠️  未配置Brave API Key，跳过")
        return []
    
    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        results = []
        queries = ["AI news today", "new AI tools 2026", "AI startup"]
        
        for query in queries:
            url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count=10"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('web', {}).get('results', []):
                    results.append({
                        "source": "Brave Search",
                        "title": item.get('title'),
                        "url": item.get('url'),
                        "description": item.get('description'),
                        "timestamp": datetime.now().isoformat()
                    })
        
        print(f"  ✅ 找到 {len(results)} 条搜索结果")
        return results
    
    except Exception as e:
        print(f"  ❌ 搜索失败：{e}")
        return []

def fetch_producthunt():
    """抓取ProductHunt AI工具"""
    print("🚀 正在抓取 ProductHunt...")
    
    try:
        feed = feedparser.parse("https://www.producthunt.com/topics/artificial-intelligence.rss")
        
        tools = []
        for entry in feed.entries[:10]:
            tools.append({
                "source": "ProductHunt",
                "title": entry.title,
                "url": entry.link,
                "description": entry.get('summary', ''),
                "timestamp": entry.get('published', datetime.now().isoformat())
            })
        
        print(f"  ✅ 找到 {len(tools)} 个AI工具")
        return tools
    
    except Exception as e:
        print(f"  ❌ 抓取失败：{e}")
        return []

def fetch_arxiv():
    """抓取arXiv AI论文"""
    print("📚 正在抓取 arXiv...")
    
    try:
        feeds = [
            "http://export.arxiv.org/rss/cs.AI",
            "http://export.arxiv.org/rss/cs.CL",
            "http://export.arxiv.org/rss/cs.LG"
        ]
        
        papers = []
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                papers.append({
                    "source": "arXiv",
                    "title": entry.title,
                    "url": entry.link,
                    "description": entry.get('summary', ''),
                    "timestamp": entry.get('published', datetime.now().isoformat())
                })
        
        print(f"  ✅ 找到 {len(papers)} 篇论文")
        return papers
    
    except Exception as e:
        print(f"  ❌ 抓取失败：{e}")
        return []

def fetch_techcrunch():
    """抓取TechCrunch AI新闻"""
    print("📰 正在抓取 TechCrunch...")
    
    try:
        feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
        
        news = []
        for entry in feed.entries[:10]:
            news.append({
                "source": "TechCrunch",
                "title": entry.title,
                "url": entry.link,
                "description": entry.get('summary', ''),
                "timestamp": entry.get('published', datetime.now().isoformat())
            })
        
        print(f"  ✅ 找到 {len(news)} 条新闻")
        return news
    
    except Exception as e:
        print(f"  ❌ 抓取失败：{e}")
        return []

# ============================================
# 数据处理模块
# ============================================

def calculate_heat(item: Dict) -> int:
    """计算热度分数"""
    heat = 0
    
    # HackerNews热度
    if item['source'] == 'HackerNews':
        heat = item.get('score', 0) + item.get('comments', 0) * 2
    
    # 其他来源基础分
    else:
        heat = 100
    
    # 时效性加成
    try:
        timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        hours_ago = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
        if hours_ago < 24:
            heat *= 2
        elif hours_ago < 72:
            heat *= 1.5
    except:
        pass
    
    return int(heat)

def classify_topic(title: str, description: str = "") -> List[str]:
    """分类到内容线"""
    text = (title + " " + description).lower()
    
    categories = []
    
    # AI科普关键词
    if any(kw in text for kw in ['explain', 'understand', 'what is', 'how does', 'introduction']):
        categories.append("AI科普")
    
    # AI工具关键词
    if any(kw in text for kw in ['tool', 'app', 'software', 'platform', 'api', 'product']):
        categories.append("AI工具")
    
    # AI编程关键词
    if any(kw in text for kw in ['code', 'coding', 'programming', 'developer', 'github', 'open source']):
        categories.append("AI编程")
    
    # AI出海创业关键词
    if any(kw in text for kw in ['startup', 'funding', 'market', 'business', 'revenue', 'valuation']):
        categories.append("AI出海创业")
    
    # 默认分类
    if not categories:
        categories.append("AI科普")
    
    return categories

def deduplicate(items: List[Dict]) -> List[Dict]:
    """去重"""
    seen_titles = set()
    unique_items = []
    
    for item in items:
        title_lower = item['title'].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_items.append(item)
    
    return unique_items

# ============================================
# 报告生成模块
# ============================================

def generate_report(items: List[Dict]) -> str:
    """生成Markdown报告"""
    
    # 按热度排序
    items_with_heat = []
    for item in items:
        item['heat'] = calculate_heat(item)
        item['categories'] = classify_topic(item['title'], item.get('description', ''))
        items_with_heat.append(item)
    
    items_sorted = sorted(items_with_heat, key=lambda x: x['heat'], reverse=True)
    
    # 分级
    high_heat = [x for x in items_sorted if x['heat'] >= TRENDING_THRESHOLD['high']]
    medium_heat = [x for x in items_sorted if TRENDING_THRESHOLD['medium'] <= x['heat'] < TRENDING_THRESHOLD['high']]
    low_heat = [x for x in items_sorted if TRENDING_THRESHOLD['low'] <= x['heat'] < TRENDING_THRESHOLD['medium']]
    
    # 生成报告
    report = []
    report.append(f"# AI热点日报")
    report.append(f"")
    report.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"> 数据源：HackerNews, ProductHunt, arXiv, TechCrunch, Brave Search")
    report.append(f"> 总计：{len(items_sorted)} 条热点")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # 高热度
    report.append(f"## 🔥🔥🔥 高热度（{len(high_heat)}条）")
    report.append(f"")
    for i, item in enumerate(high_heat, 1):
        report.append(f"### {i}. {item['title']}")
        report.append(f"")
        report.append(f"- **来源**：{item['source']}")
        report.append(f"- **热度**：{item['heat']}")
        report.append(f"- **推荐内容线**：{', '.join(item['categories'])}")
        report.append(f"- **链接**：{item['url']}")
        if item.get('description'):
            report.append(f"- **简介**：{item['description'][:200]}...")
        report.append(f"")
    
    # 中热度
    if medium_heat:
        report.append(f"## 🔥 中热度（{len(medium_heat)}条）")
        report.append(f"")
        for i, item in enumerate(medium_heat, 1):
            report.append(f"{i}. **{item['title']}** ({item['source']}, 热度{item['heat']})")
            report.append(f"   - 推荐：{', '.join(item['categories'])}")
            report.append(f"   - {item['url']}")
            report.append(f"")
    
    # 低热度（仅列标题）
    if low_heat:
        report.append(f"## 💤 低热度（{len(low_heat)}条）")
        report.append(f"")
        for item in low_heat[:10]:
            report.append(f"- {item['title']} ({item['source']})")
        report.append(f"")
    
    # 统计
    report.append(f"---")
    report.append(f"")
    report.append(f"## 📊 统计")
    report.append(f"")
    
    category_counter = Counter()
    for item in items_sorted:
        for cat in item['categories']:
            category_counter[cat] += 1
    
    report.append(f"**内容线分布**：")
    for cat, count in category_counter.most_common():
        report.append(f"- {cat}: {count}条")
    report.append(f"")
    
    source_counter = Counter([x['source'] for x in items_sorted])
    report.append(f"**数据源分布**：")
    for source, count in source_counter.most_common():
        report.append(f"- {source}: {count}条")
    
    return "\n".join(report)

# ============================================
# 主程序
# ============================================

def run_monitor():
    """运行监控"""
    print(f"\n{'='*60}")
    print(f"🤖 AI热点监控系统")
    print(f"{'='*60}\n")
    
    all_items = []
    
    # 采集数据
    all_items.extend(fetch_hackernews())
    all_items.extend(fetch_brave_search())
    all_items.extend(fetch_producthunt())
    all_items.extend(fetch_arxiv())
    all_items.extend(fetch_techcrunch())
    
    # 去重
    all_items = deduplicate(all_items)
    
    print(f"\n{'='*60}")
    print(f"📊 数据采集完成：共 {len(all_items)} 条（去重后）")
    print(f"{'='*60}\n")
    
    # 生成报告
    report = generate_report(all_items)
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"ai_trending_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{report_file}\n")
    
    # 保存JSON
    json_file = f"ai_trending_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存：{json_file}\n")
    
    return report_file, json_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        print("🔄 后台运行模式（每4小时执行一次）")
        print("按 Ctrl+C 停止\n")
        
        while True:
            try:
                run_monitor()
                print(f"\n⏰ 下次运行时间：{(datetime.now() + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(4 * 3600)
            except KeyboardInterrupt:
                print("\n\n👋 监控已停止")
                break
    else:
        run_monitor()
```

---

## 📖 使用指南

### 第一步：配置API Key

**必需**：
- ✅ Brave Search API（免费，推荐）
  - 注册：https://brave.com/search/api/
  - 免费额度：2000次/月

**可选**（增强功能）：
- ⚠️ Reddit API（需要创建应用）
- ⚠️ Twitter API v2（付费，$100/月起）

### 第二步：安装依赖

```bash
pip install requests feedparser
```

### 第三步：运行监控

```bash
# 运行一次
python ai_monitor.py

# 后台运行（每4小时）
python ai_monitor.py --daemon
```

### 第四步：查看报告

生成的文件：
- `ai_trending_20260221_120000.md`（Markdown报告）
- `ai_trending_20260221_120000.json`（原始数据）

### 第五步：定时任务（推荐）

**Linux/Mac（使用cron）**：
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天早上9点运行）
0 9 * * * cd /path/to/workspace && python ai_monitor.py
```

**Windows（使用任务计划程序）**：
1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天早上9点
4. 操作：启动程序 `python.exe ai_monitor.py`

---

## 📊 输出示例

### Markdown报告示例

```markdown
# AI热点日报

> 生成时间：2026-02-21 12:00:00
> 数据源：HackerNews, ProductHunt, arXiv, TechCrunch, Brave Search
> 总计：25 条热点

---

## 🔥🔥🔥 高热度（3条）

### 1. Google Unveils Project Genie: AI World Model

- **来源**：HackerNews
- **热度**：8750
- **推荐内容线**：AI科普, AI出海创业
- **链接**：https://...
- **简介**：Google发布世界模型Project Genie...

### 2. Anthropic Claude Now Supports 10M Token Context

- **来源**：TechCrunch
- **热度**：6200
- **推荐内容线**：AI工具, AI编程
- **链接**：https://...

...
```

---

## 🔧 高级配置

### 自定义关键词

编辑`ai_monitor.py`：
```python
AI_KEYWORDS = [
    "你的自定义关键词1",
    "你的自定义关键词2",
    # ...
]
```

### 调整热度阈值

```python
TRENDING_THRESHOLD = {
    "high": 10000,   # 调高阈值
    "medium": 2000,
    "low": 500
}
```

### 增加新数据源

```python
def fetch_your_source():
    """你的自定义数据源"""
    # 实现抓取逻辑
    return []

# 在run_monitor()中调用
all_items.extend(fetch_your_source())
```

---

## 🎯 下一步优化

- [ ] 增加机器学习预测（基于历史数据预测爆款概率）
- [ ] 企业微信/邮件推送
- [ ] 可视化Dashboard（Flask + Chart.js）
- [ ] 多语言支持（中文热点追踪）
- [ ] 竞品追踪（特定公司/产品动态）

---

**文档状态**：✅已完成  
**关联文档**：
- `ai_monitor.py`（监控脚本）
- `topic_scorer.py`（评分脚本）
- `topic_selection_system.md`（筛选标准）
