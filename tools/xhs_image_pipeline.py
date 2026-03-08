#!/usr/bin/env python3
"""
小红书图片生成全流程脚本
用法：python3 xhs_image_pipeline.py <文章.md路径>

流程：
  1. 读取文章内容
  2. 调用 Claude API 生成图片 prompts（8张图）
  3. 调用 GrsAI API 批量生成图片（nano-banana-pro）
  4. 下载图片到本地 output 目录

依赖：pip install aiohttp python-dotenv anthropic
"""

import asyncio
import aiohttp
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── 加载环境变量 ───────────────────────────────────────────────
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

GRSAI_API_KEY = os.getenv("GRSAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ─── GrsAI 配置 ──────────────────────────────────────────────────
GRSAI_BASE_URL = "https://grsai.dakka.com.cn"
GRSAI_SUBMIT_URL = f"{GRSAI_BASE_URL}/v1/draw/nano-banana"
GRSAI_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GRSAI_API_KEY}"
}
ASPECT_RATIO = "3:4"
MODEL = "nano-banana-pro"
MAX_CONCURRENT = 3
POLL_INTERVAL = 5
POLL_TIMEOUT = 300

# ─── baoyu-xhs-images 风格规范（内嵌，无需外部文件）───────────────
STYLE_SYSTEM_PROMPT = """你是一个专业的小红书图文内容策划师，擅长将文章转化为适合 nano banana pro 生成的图片 prompt。

## 输出格式要求

输出一个 JSON 数组，包含 8 个图片任务，格式如下：
```json
[
  {
    "name": "图01_封面",
    "prompt": "完整的英文 prompt 内容"
  },
  ...
]
```

## 每个 prompt 的固定结构

每个 prompt 必须包含以下完整内容（英文）：

```
Create a Xiaohongshu (Little Red Book) style infographic following these guidelines:

**Image Specifications**: Portrait 3:4, Hand-drawn illustration style, ALL text in Chinese

**Core Principles**:
- Hand-drawn quality throughout - NO realistic or photographic elements
- Keep information concise, highlight keywords and core concepts
- Use ample whitespace for easy visual scanning
- Maintain clear visual hierarchy

**Text Style**: ALL text MUST be hand-drawn style, main titles prominent, use highlighter effects on keywords

**Style**: Notion — Black (#1A1A1A)/white (#FFFFFF) base, pastel blue (#A8D4F0)/yellow (#F9E79F)/pink (#FADBD8) accents, simple line doodles, maximum whitespace, single-weight ink lines

**Layout**: [根据内容选择: Sparse/Balanced/Comparison/List/Flow/Dense]

**Content**:
[中文内容：标题、要点、金句、互动引导等]

**Visual Concept**:
[具体的画面描述：人物、图标、构图、颜色分布等]

Please use nano banana pro to generate the infographic based on the specifications above.
```

## 8张图的结构安排

1. **封面**（Sparse布局）：强冲击力标题 + 悬念感，极简留白
2. **人物/背景介绍**（Balanced布局）：谁做了什么，关键数字
3. **核心观点1**（Comparison/List布局）：文章最重要的论点
4. **核心观点2**（List/Dense布局）：第二个重要论点
5. **核心观点3**（Flow/Dense布局）：第三个重要论点
6. **金句/深度思考**（Sparse/Quote布局）：最有共鸣的一句话
7. **总结/启示**（Balanced/List布局）：读者能带走什么
8. **结尾互动**（Sparse布局）：引发思考的问题 + 评论引导

## 注意事项
- prompt 中的 Content 部分用中文（这是图片里要显示的文字）
- prompt 中的描述性文字（Style/Layout/Visual Concept）用英文
- 每张图的 Visual Concept 要具体，包含手绘人物、图标、构图细节
- 封面和结尾形成情绪闭环
"""

# ─── Step 1: 用 Claude 生成 prompts ──────────────────────────────
def generate_prompts_with_claude(article_content: str) -> list[dict]:
    """调用 Claude API 生成图片 prompts"""
    print("\n🤖 正在调用 Claude 生成图片 prompts...")

    try:
        import anthropic
    except ImportError:
        print("❌ 未安装 anthropic，请运行：pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = f"""请为以下文章生成 8 张小红书图片的 prompt，输出 JSON 格式：

<article>
{article_content}
</article>

请严格按照系统提示的格式输出 JSON 数组，不要有任何额外说明。"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        system=STYLE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    response_text = message.content[0].text.strip()

    # 提取 JSON
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 尝试直接解析
        json_str = response_text

    try:
        tasks = json.loads(json_str)
        print(f"✅ 成功生成 {len(tasks)} 个图片任务")
        return tasks
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}")
        print(f"原始响应：{response_text[:500]}")
        sys.exit(1)


# ─── Step 2: 保存 prompts.md（备份用）───────────────────────────
def save_prompts_md(tasks: list[dict], output_dir: Path, article_name: str) -> Path:
    """将 prompts 保存为 md 文件（供备份和手动使用）"""
    lines = [f"# {article_name} · 小红书图片 Prompts\n\n"]
    lines.append("> 由 xhs_image_pipeline.py 自动生成\n\n---\n\n")

    for task in tasks:
        lines.append(f"## {task['name']}\n\n")
        lines.append(f"{task['prompt']}\n\n---\n\n")

    md_path = output_dir / f"{article_name}_image_prompts.md"
    md_path.write_text("".join(lines), encoding="utf-8")
    print(f"📄 prompts.md 已保存：{md_path}")
    return md_path


# ─── Step 3: 提交单个生成任务 ────────────────────────────────────
async def submit_task(session: aiohttp.ClientSession, task: dict, index: int) -> dict:
    """提交生成任务，返回任务ID"""
    payload = {
        "model": MODEL,
        "prompt": task["prompt"],
        "aspectRatio": ASPECT_RATIO,
        "webHook": "-1"
    }
    try:
        async with session.post(
            GRSAI_SUBMIT_URL,
            headers=GRSAI_HEADERS,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            task_id = data.get("id") or data.get("taskId")
            if task_id:
                print(f"  📤 [{index+1:02d}] 已提交「{task['name']}」→ {task_id}")
                return {"index": index, "name": task["name"], "task_id": task_id, "status": "pending"}
            else:
                print(f"  ❌ [{index+1:02d}] 提交失败「{task['name']}」: {data}")
                return {"index": index, "name": task["name"], "task_id": None, "status": "failed", "error": str(data)}
    except Exception as e:
        print(f"  ❌ [{index+1:02d}] 提交异常「{task['name']}」: {e}")
        return {"index": index, "name": task["name"], "task_id": None, "status": "failed", "error": str(e)}


# ─── Step 4: 轮询任务状态 ────────────────────────────────────────
async def poll_task(session: aiohttp.ClientSession, task_result: dict) -> dict:
    """轮询直到任务完成，返回图片URL"""
    if not task_result.get("task_id"):
        return task_result

    task_id = task_result["task_id"]
    name = task_result["name"]
    idx = task_result["index"]
    elapsed = 0

    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        try:
            url = f"{GRSAI_BASE_URL}/v1/draw/result/{task_id}"
            async with session.get(url, headers=GRSAI_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                status = data.get("status", "")
                progress = data.get("progress", 0)

                if progress > 0 or status:
                    print(f"  ⏳ [{idx+1:02d}] 「{name}」{progress}% ({elapsed}s)")

                if status == "succeeded":
                    results = data.get("results", [])
                    if results:
                        img_url = results[0].get("url")
                        print(f"  ✅ [{idx+1:02d}] 「{name}」完成！")
                        return {**task_result, "status": "succeeded", "img_url": img_url}

                elif status == "failed":
                    print(f"  ❌ [{idx+1:02d}] 「{name}」生成失败")
                    return {**task_result, "status": "failed"}

        except Exception as e:
            print(f"  ⚠️  [{idx+1:02d}] 轮询异常「{name}」: {e}")

    print(f"  ⏰ [{idx+1:02d}] 「{name}」超时（{POLL_TIMEOUT}s）")
    return {**task_result, "status": "timeout"}


# ─── Step 5: 下载图片 ────────────────────────────────────────────
async def download_image(session: aiohttp.ClientSession, task_result: dict, output_dir: Path) -> str | None:
    """下载图片到本地，返回文件路径"""
    if task_result.get("status") != "succeeded":
        return None

    img_url = task_result.get("img_url")
    name = task_result["name"]
    idx = task_result["index"]

    safe_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', name)
    filename = f"{idx+1:02d}_{safe_name}.png"
    filepath = output_dir / filename

    try:
        async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                filepath.write_bytes(await resp.read())
                print(f"  💾 [{idx+1:02d}] 已保存：{filename}")
                return str(filepath)
            else:
                print(f"  ❌ [{idx+1:02d}] 下载失败「{name}」: HTTP {resp.status}")
                return None
    except Exception as e:
        print(f"  ❌ [{idx+1:02d}] 下载异常「{name}」: {e}")
        return None


# ─── 主流程 ──────────────────────────────────────────────────────
async def main(article_path: str):
    print(f"\n{'='*60}")
    print(f"🍌 小红书图片生成全流程")
    print(f"{'='*60}")

    # 检查必要配置
    if not GRSAI_API_KEY:
        print("❌ 未找到 GRSAI_API_KEY，请在 .env 中配置")
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        print("❌ 未找到 ANTHROPIC_API_KEY，请在 .env 中配置")
        sys.exit(1)

    # 读取文章
    article_file = Path(article_path)
    if not article_file.exists():
        print(f"❌ 文件不存在：{article_path}")
        sys.exit(1)

    article_content = article_file.read_text(encoding="utf-8")
    article_name = article_file.stem
    print(f"📄 文章：{article_name}（{len(article_content)} 字符）")

    # 创建输出目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = article_file.parent / f"{article_name}_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录：{output_dir}")

    # Step 1: 生成 prompts
    tasks = generate_prompts_with_claude(article_content)

    # Step 2: 保存 prompts.md 备份
    save_prompts_md(tasks, output_dir, article_name)

    # Step 3-5: 批量生成并下载图片
    print(f"\n🚀 开始批量生成图片（并发数: {MAX_CONCURRENT}）...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with aiohttp.ClientSession() as session:
        # 提交所有任务
        async def submit_with_sem(task, idx):
            async with semaphore:
                return await submit_task(session, task, idx)

        submitted = await asyncio.gather(*[submit_with_sem(t, i) for i, t in enumerate(tasks)])

        # 轮询所有任务
        print(f"\n⏳ 等待生成完成...")
        completed = await asyncio.gather(*[poll_task(session, r) for r in submitted])

        # 下载所有图片
        print(f"\n💾 开始下载图片...")
        saved_files = await asyncio.gather(*[download_image(session, r, output_dir) for r in completed])

    # 统计结果
    success = [f for f in saved_files if f]
    failed_tasks = [r["name"] for r, f in zip(completed, saved_files) if not f]

    print(f"\n{'='*60}")
    print(f"✅ 全部完成！")
    print(f"   成功：{len(success)}/{len(tasks)} 张")
    if failed_tasks:
        print(f"   失败：{', '.join(failed_tasks)}")
    print(f"   保存位置：{output_dir}")
    print(f"{'='*60}\n")

    # 保存报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "article": article_path,
        "output_dir": str(output_dir),
        "total": len(tasks),
        "success": len(success),
        "failed": len(failed_tasks),
        "files": success
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    return output_dir


# ─── 入口 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 xhs_image_pipeline.py <文章.md路径>")
        print("示例：python3 xhs_image_pipeline.py /data/workspace/.draft/2026-03-07/龙虾之父访谈_小红书版.md")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
