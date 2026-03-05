#!/usr/bin/env python3
"""
AIContentFlow - Notion 发布模块
功能：
  1. 将 Markdown 文章上传到「📥 草稿箱」（发布前暂存）
  2. 归档：将草稿箱中的文章移动到正式内容库，并更新索引
  3. 上传后自动重建「📚 文章归档索引」页面

用法：
  # 上传到草稿箱（默认）
  python3 notion_publisher.py --file /path/to/article.md
  python3 notion_publisher.py --file /path/to/article.md --type wechat

  # 归档：将草稿箱文章移动到正式内容库（发布后执行）
  python3 notion_publisher.py --archive <草稿页面ID>
  python3 notion_publisher.py --archive <草稿页面ID> --type wechat

  # 仅重建索引
  python3 notion_publisher.py --rebuild-index

作者：AIContentFlow
版本：2.0.0
"""

import os
import re
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional, Any

# ============================================================================
# 配置
# ============================================================================

TOKEN = os.getenv("NOTION_TOKEN", "")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")     # 正式内容库
INDEX_PAGE_ID = os.getenv("NOTION_INDEX_PAGE_ID", "")       # 归档索引页
DRAFTS_PAGE_ID = os.getenv("NOTION_DRAFTS_PAGE_ID", "")     # 草稿箱

ARTICLE_TYPE_LABELS = {
    "wechat": "公众号长文",
    "xiaohongshu": "小红书版",
    "default": "文章",
}

# 文件名关键词 → 类型自动识别
TYPE_KEYWORDS = {
    "小红书": "xiaohongshu",
    "xhs": "xiaohongshu",
    "wechat": "wechat",
    "公众号": "wechat",
}

# ============================================================================
# Notion API 工具函数
# ============================================================================

def notion_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """发送 Notion API 请求"""
    url = f"https://api.notion.com/v1/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"  ❌ Notion API 错误 [{e.code}]: {err.get('message', err)}")
        return err


def get_page_children(page_id: str) -> List[Dict]:
    """获取页面下所有子块（自动翻页）"""
    results = []
    cursor = None
    while True:
        endpoint = f"blocks/{page_id}/children?page_size=100"
        if cursor:
            endpoint += f"&start_cursor={cursor}"
        resp = notion_request("GET", endpoint)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


def delete_block(block_id: str):
    """删除一个块"""
    notion_request("DELETE", f"blocks/{block_id}")


def append_blocks(page_id: str, blocks: List[Dict], batch_size: int = 100):
    """分批追加块到页面"""
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i + batch_size]
        result = notion_request("PATCH", f"blocks/{page_id}/children", {"children": batch})
        if "results" not in result:
            print(f"  ⚠️  第 {i // batch_size + 1} 批追加异常: {result.get('message', result)}")


# ============================================================================
# Markdown → Notion Blocks 转换
# ============================================================================

def parse_inline(text: str) -> List[Dict]:
    """解析行内格式：**bold**, *italic*, `code`"""
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    rich_text = []
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            rich_text.append({
                "type": "text",
                "text": {"content": part[2:-2]},
                "annotations": {"bold": True}
            })
        elif part:
            sub_parts = re.split(r"(\*[^*]+\*)", part)
            for sp in sub_parts:
                if sp.startswith("*") and sp.endswith("*") and len(sp) > 2:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": sp[1:-1]},
                        "annotations": {"italic": True}
                    })
                elif sp:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": sp}
                    })
    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]


def md_to_blocks(md_text: str, skip_first_title: bool = True) -> List[Dict]:
    """将 Markdown 文本转换为 Notion blocks 列表"""
    blocks = []
    lines = md_text.split("\n")

    for i, line in enumerate(lines):
        if i == 0 and skip_first_title and line.startswith("# "):
            continue

        if line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": parse_inline(line[3:].strip())}
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": parse_inline(line[4:].strip())}
            })
        elif line.strip() == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.startswith("> "):
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": parse_inline(line[2:].strip())}
            })
        elif re.match(r"^[-*] ", line):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_inline(line[2:].strip())}
            })
        elif re.match(r"^\d+\. ", line):
            text = re.sub(r"^\d+\. ", "", line).strip()
            blocks.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_inline(text)}
            })
        elif line.strip() == "":
            pass
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": parse_inline(line)}
            })

    return blocks


# ============================================================================
# 文章类型自动识别
# ============================================================================

def detect_article_type(file_path: str) -> str:
    """根据文件名自动识别文章类型"""
    fname = os.path.basename(file_path)
    for keyword, art_type in TYPE_KEYWORDS.items():
        if keyword.lower() in fname.lower():
            return art_type
    return "default"


def get_type_label(art_type: str) -> str:
    return ARTICLE_TYPE_LABELS.get(art_type, ARTICLE_TYPE_LABELS["default"])


# ============================================================================
# 上传文章到草稿箱
# ============================================================================

def upload_to_drafts(file_path: str, article_type: str = "default") -> Optional[Dict]:
    """
    将 Markdown 文件上传到「📥 草稿箱」，返回新建页面信息
    """
    if not DRAFTS_PAGE_ID:
        print("  ❌ 未配置 NOTION_DRAFTS_PAGE_ID，请检查 .env")
        return None

    if not os.path.exists(file_path):
        print(f"  ❌ 文件不存在: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    title_match = re.match(r"^# (.+)", content)
    title = title_match.group(1).strip() if title_match else os.path.basename(file_path).replace(".md", "")

    print(f"  📝 标题: {title}")
    print(f"  🏷️  类型: {get_type_label(article_type)}")

    blocks = md_to_blocks(content, skip_first_title=True)
    print(f"  📦 共 {len(blocks)} 个内容块")

    batch_size = 100
    first_batch = blocks[:batch_size]
    rest_batches = [blocks[i:i + batch_size] for i in range(batch_size, len(blocks), batch_size)]

    page_data = {
        "parent": {"page_id": DRAFTS_PAGE_ID},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": first_batch
    }

    result = notion_request("POST", "pages", page_data)
    if "id" not in result:
        print(f"  ❌ 页面创建失败: {result.get('message', result)}")
        return None

    page_id = result["id"]
    page_url = result.get("url", f"https://notion.so/{page_id.replace('-', '')}")

    for idx, batch in enumerate(rest_batches, 2):
        print(f"  📦 追加第 {idx} 批 ({len(batch)} 块)...")
        append_blocks(page_id, batch)

    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"  ✅ 已上传到草稿箱！")
    print(f"  🔗 {page_url}")
    print(f"  💡 发布后请执行归档：python3 notion_publisher.py --archive {page_id}")

    return {
        "id": page_id,
        "url": page_url,
        "title": title,
        "type": article_type,
        "date": date_str,
        "location": "drafts",
    }


# ============================================================================
# 归档：草稿箱 → 正式内容库
# ============================================================================

def archive_draft(draft_page_id: str, article_type: str = None) -> Optional[Dict]:
    """
    将草稿箱中的页面移动到正式内容库（PARENT_PAGE_ID），并重建索引。
    Notion API 不支持直接移动页面，采用「读取内容 → 在正式库创建 → 删除草稿」方案。
    """
    if not PARENT_PAGE_ID:
        print("  ❌ 未配置 NOTION_PARENT_PAGE_ID，请检查 .env")
        return None

    print(f"  🔍 读取草稿页面: {draft_page_id}")

    # 获取草稿页面信息
    draft_detail = notion_request("GET", f"pages/{draft_page_id}")
    if "id" not in draft_detail:
        print(f"  ❌ 草稿页面不存在或无权访问: {draft_page_id}")
        return None

    # 提取标题
    title_props = draft_detail.get("properties", {}).get("title", {}).get("title", [])
    title = "".join([t.get("plain_text", "") for t in title_props]) or "未命名文章"

    # 自动识别类型
    if not article_type:
        title_lower = title.lower()
        article_type = "default"
        for keyword, t in TYPE_KEYWORDS.items():
            if keyword.lower() in title_lower:
                article_type = t
                break

    print(f"  📝 标题: {title}")
    print(f"  🏷️  类型: {get_type_label(article_type)}")

    # 获取草稿内容块
    print(f"  📦 读取草稿内容...")
    draft_blocks = get_page_children(draft_page_id)

    # 过滤掉不可复制的块类型（child_page、child_database 等）
    copyable_types = {
        "paragraph", "heading_1", "heading_2", "heading_3",
        "bulleted_list_item", "numbered_list_item", "to_do",
        "toggle", "quote", "callout", "divider", "code",
        "image", "bookmark", "embed"
    }
    content_blocks = []
    for block in draft_blocks:
        btype = block.get("type")
        if btype in copyable_types:
            # 重新构建 block（去掉 id、created_time 等只读字段）
            block_content = block.get(btype, {})
            content_blocks.append({
                "object": "block",
                "type": btype,
                btype: block_content
            })

    print(f"  📦 共 {len(content_blocks)} 个可复制内容块")

    # 在正式内容库创建新页面
    batch_size = 100
    first_batch = content_blocks[:batch_size]
    rest_batches = [content_blocks[i:i + batch_size] for i in range(batch_size, len(content_blocks), batch_size)]

    page_data = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": first_batch
    }

    print(f"  📤 在正式内容库创建页面...")
    result = notion_request("POST", "pages", page_data)
    if "id" not in result:
        print(f"  ❌ 正式页面创建失败: {result.get('message', result)}")
        return None

    new_page_id = result["id"]
    new_page_url = result.get("url", f"https://notion.so/{new_page_id.replace('-', '')}")

    for idx, batch in enumerate(rest_batches, 2):
        print(f"  📦 追加第 {idx} 批 ({len(batch)} 块)...")
        append_blocks(new_page_id, batch)

    # 删除草稿（归档后移除）
    print(f"  🗑️  删除草稿箱中的草稿...")
    del_result = notion_request("PATCH", f"pages/{draft_page_id}", {"archived": True})
    if del_result.get("archived"):
        print(f"  ✅ 草稿已归档删除")
    else:
        print(f"  ⚠️  草稿删除失败，请手动删除: {draft_page_id}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    created_time = draft_detail.get("created_time", "")
    if created_time:
        date_str = created_time[:10]

    print(f"  ✅ 归档成功！")
    print(f"  🔗 {new_page_url}")

    return {
        "id": new_page_id,
        "url": new_page_url,
        "title": title,
        "type": article_type,
        "date": date_str,
        "location": "published",
    }


# ============================================================================
# 重建「📚 文章归档索引」页面
# ============================================================================

def rebuild_index(new_article: Optional[Dict] = None):
    """
    重建 Notion 索引页：
    - 扫描正式内容库下所有子页面
    - 按日期分组，倒序排列
    - 每篇文章使用 mention 链接（可点击跳转）
    - 显示文章类型标签
    """
    print("\n🔄 正在重建归档索引页...")

    children = get_page_children(PARENT_PAGE_ID)
    sub_pages = []
    for block in children:
        if block.get("type") == "child_page":
            page_id = block["id"]
            page_title = block["child_page"]["title"]
            if page_id.replace("-", "") == INDEX_PAGE_ID.replace("-", ""):
                continue
            sub_pages.append({
                "id": page_id,
                "title": page_title,
            })

    print(f"  📋 发现 {len(sub_pages)} 个子页面（不含索引页本身）")

    enriched = []
    for page in sub_pages:
        page_detail = notion_request("GET", f"pages/{page['id']}")
        created_time = page_detail.get("created_time", "")
        date_str = created_time[:10] if created_time else datetime.now().strftime("%Y-%m-%d")

        art_type = "default"
        title_lower = page["title"].lower()
        for keyword, t in TYPE_KEYWORDS.items():
            if keyword.lower() in title_lower:
                art_type = t
                break

        enriched.append({
            "id": page["id"],
            "title": page["title"],
            "date": date_str,
            "type": art_type,
        })

    if new_article:
        for p in enriched:
            if p["id"].replace("-", "") == new_article["id"].replace("-", ""):
                p["type"] = new_article["type"]
                p["date"] = new_article["date"]
                break

    by_date = defaultdict(list)
    for p in enriched:
        by_date[p["date"]].append(p)

    existing_blocks = get_page_children(INDEX_PAGE_ID)
    print(f"  🗑️  清空旧内容（{len(existing_blocks)} 块）...")
    for block in existing_blocks:
        delete_block(block["id"])

    total = len(enriched)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = []

    blocks.append({
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {
                "content": f"按日期目录整理，每日生成的文章自动归档。共 {total} 篇文章。最后更新：{now_str}"
            }}],
            "icon": {"type": "emoji", "emoji": "📚"},
            "color": "blue_background"
        }
    })
    blocks.append({"object": "block", "type": "divider", "divider": {}})

    for date_str in sorted(by_date.keys(), reverse=True):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            date_label = dt.strftime("%Y年%m月%d日")
        except ValueError:
            date_label = date_str

        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"📅 {date_label}"}}]}
        })

        for article in by_date[date_str]:
            type_label = get_type_label(article["type"])
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"[{type_label}]  "},
                            "annotations": {"bold": True, "color": "blue"}
                        },
                        {
                            "type": "mention",
                            "mention": {
                                "type": "page",
                                "page": {"id": article["id"]}
                            }
                        }
                    ]
                }
            })

    blocks.append({"object": "block", "type": "divider", "divider": {}})

    append_blocks(INDEX_PAGE_ID, blocks)

    index_url = f"https://notion.so/{INDEX_PAGE_ID.replace('-', '')}"
    print(f"  ✅ 索引页重建完成！共 {total} 篇文章")
    print(f"  🔗 {index_url}")
    return index_url


# ============================================================================
# 主入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="AIContentFlow - Notion 发布工具")
    parser.add_argument("--file", "-f", help="要上传到草稿箱的 Markdown 文件路径")
    parser.add_argument("--type", "-t", choices=list(ARTICLE_TYPE_LABELS.keys()),
                        default=None, help="文章类型（wechat/xiaohongshu/default）")
    parser.add_argument("--archive", "-a", metavar="DRAFT_PAGE_ID",
                        help="归档：将草稿箱页面移动到正式内容库（填草稿页面ID）")
    parser.add_argument("--rebuild-index", action="store_true",
                        help="仅重建索引页，不上传新文章")
    args = parser.parse_args()

    # 仅重建索引
    if args.rebuild_index and not args.file and not args.archive:
        rebuild_index()
        return

    # 归档流程
    if args.archive:
        print(f"\n{'='*60}")
        print(f"  AIContentFlow - 归档草稿到正式内容库")
        print(f"{'='*60}")
        print(f"  草稿 ID: {args.archive}")
        print()

        print("📦 步骤 1/2：归档草稿...")
        archived = archive_draft(args.archive, args.type)

        if not archived:
            print("❌ 归档失败，中止")
            return

        print("\n🔄 步骤 2/2：更新归档索引页...")
        index_url = rebuild_index(archived)

        print(f"\n{'='*60}")
        print(f"  🎉 归档完成！")
        print(f"  📝 正式文章: {archived['url']}")
        print(f"  📚 索引: {index_url}")
        print(f"{'='*60}\n")
        return

    # 上传到草稿箱
    if not args.file:
        parser.print_help()
        return

    article_type = args.type or detect_article_type(args.file)

    print(f"\n{'='*60}")
    print(f"  AIContentFlow - 上传到草稿箱")
    print(f"{'='*60}")
    print(f"  文件: {args.file}")
    print(f"  类型: {get_type_label(article_type)}")
    print()

    print("📤 上传文章到草稿箱...")
    draft = upload_to_drafts(args.file, article_type)

    if not draft:
        print("❌ 上传失败，中止")
        return

    print(f"\n{'='*60}")
    print(f"  🎉 已上传到草稿箱！")
    print(f"  📝 草稿链接: {draft['url']}")
    print(f"  💡 发布后归档命令：")
    print(f"     python3 publisher/notion_publisher.py --archive {draft['id']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
