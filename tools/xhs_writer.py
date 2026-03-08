#!/usr/bin/env python3
"""
小红书正文生成脚本
输入：原始文章 .md 文件
输出：小红书正文（150-250字，精简版）+ 话题标签

规范：
- 字数：150-250字
- 结构：Hook（1-2句）→ 核心感受/发现（2-4句）→ 互动引导（1句）
- 风格：口语化，多 emoji，不解释只陈述
- 标签：5-8 个话题标签
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


def get_system_prompt():
    return """你是一位小红书内容专家，擅长将深度文章提炼成打动人心的短文字。

## 小红书正文写作规范

### 核心原则
图片是主角，文字只留情绪和互动。
小红书用户浏览路径：封面图 → 滑动看图 → 最后才看文字。

### 字数与结构
- 字数：150-250字（不含标签）
- 结构：
  1. Hook（1-2句）：制造悬念或强烈共鸣，抓住读者
  2. 核心感受/发现（2-4句）：最打动人的事实/金句，不解释，只陈述
  3. 互动引导（1句）：引发评论或收藏
- 标签：5-8 个话题标签，放在正文末尾

### 保留 vs 删除
✅ 保留：
- 制造悬念/共鸣的开场句
- 最打动人的 1-2 个金句（不解释，只陈述）
- 互动引导结尾

❌ 删掉：
- 背景铺垫、来龙去脉
- 逻辑推导过程
- 总结归纳、观点解释

### 写作风格
- 具体事实代替抽象描述（如「发布3天登上 GitHub Trending」而非「引起广泛关注」）
- 主动语态，短句为主
- 减少过渡词，直接说事实
- 口语化，多用 emoji
- 适当提问与读者互动

### 输出格式
直接输出小红书正文内容，不要加任何解释或说明。
格式：
[正文内容，含 emoji]

#话题标签1 #话题标签2 #话题标签3 ...
"""


def generate_xhs_text(article_content: str, article_title: str) -> str:
    """调用 Claude API 生成小红书正文"""
    try:
        import anthropic
    except ImportError:
        print("❌ 未安装 anthropic 库，请运行：pip install anthropic")
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 未配置 ANTHROPIC_API_KEY，请在 .env 文件中添加")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"""请根据以下文章，生成一篇小红书正文。

文章标题：{article_title}

文章内容：
{article_content}

要求：
- 字数 150-250 字（不含标签）
- 只留最动人、最核心的内容
- 内容靠图片表达，文字只留情绪和互动
- 口语化，多用 emoji
- 结尾加 5-8 个话题标签
"""

    print("⏳ 正在生成小红书正文...")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=get_system_prompt(),
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def save_output(article_path: Path, xhs_text: str) -> Path:
    """保存输出文件"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("/data/workspace/AIContentFlow/outputs/archive") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = article_path.stem.replace("_小红书版", "").replace("_原文", "")
    output_path = output_dir / f"{stem}_小红书正文.md"

    content = f"""# {stem} — 小红书正文

> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}  
> 字数：{len(xhs_text.replace(' ', '').replace('#', '').replace('\n', ''))} 字（含emoji）  
> 原始文章：{article_path.name}

---

{xhs_text}
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法：python3 xhs_writer.py <文章路径.md>")
        print("示例：python3 xhs_writer.py /data/workspace/.draft/2026-03-08/龙虾之父访谈.md")
        sys.exit(1)

    article_path = Path(sys.argv[1])
    if not article_path.exists():
        print(f"❌ 文件不存在：{article_path}")
        sys.exit(1)

    # 加载 .env
    env_path = Path("/data/workspace/AIContentFlow/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    # 读取文章
    article_content = article_path.read_text(encoding="utf-8")
    article_title = article_path.stem

    print(f"📄 读取文章：{article_path.name}")
    print(f"   字数：{len(article_content)} 字")

    # 生成正文
    xhs_text = generate_xhs_text(article_content, article_title)

    # 统计字数（去掉标签和空白）
    text_only = xhs_text.split("#")[0].strip()
    char_count = len(text_only.replace(" ", "").replace("\n", ""))

    print(f"\n{'='*50}")
    print("✅ 小红书正文生成完成")
    print(f"{'='*50}")
    print(f"\n{xhs_text}")
    print(f"\n{'='*50}")
    print(f"📊 正文字数：约 {char_count} 字（不含标签）")

    # 字数提示
    if char_count < 150:
        print("⚠️  字数偏少（< 150字），建议补充一些细节")
    elif char_count > 250:
        print("⚠️  字数偏多（> 250字），建议再精简")
    else:
        print("✅ 字数符合规范（150-250字）")

    # 保存输出
    output_path = save_output(article_path, xhs_text)
    print(f"\n💾 已保存到：{output_path}")
    print("\n下一步：告诉 Knot「帮我为这篇文章生成图片 prompts」")


if __name__ == "__main__":
    main()
