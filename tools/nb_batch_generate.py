#!/usr/bin/env python3
"""
Nano Banana Pro 批量图片生成脚本
用法：python3 nb_batch_generate.py <prompts.md文件路径>
依赖：pip install aiohttp python-dotenv
"""

import asyncio
import aiohttp
import re
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── 加载环境变量 ───────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("GRSAI_API_KEY")
if not API_KEY:
    print("❌ 未找到 GRSAI_API_KEY，请在 .env 文件中配置：GRSAI_API_KEY=your_key")
    sys.exit(1)

# ─── 配置 ────────────────────────────────────────────────────────
BASE_URL = "https://grsai.dakka.com.cn"          # 国内直连节点
ENDPOINT = f"{BASE_URL}/v1/draw/nano-banana"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
ASPECT_RATIO = "3:4"                              # 小红书竖版
MODEL = "nano-banana-pro"                         # 使用 Pro 版
MAX_CONCURRENT = 3                                # 最大并发数（避免限速）
POLL_INTERVAL = 5                                 # 轮询间隔（秒）
POLL_TIMEOUT = 300                                # 最大等待时间（秒）


# ─── 解析 prompts.md ─────────────────────────────────────────────
def parse_prompts_md(md_path: str) -> list[dict]:
    """
    从 prompts.md 中解析所有图片任务
    返回：[{"name": "封面图", "prompt": "...英文prompt..."}, ...]
    """
    content = Path(md_path).read_text(encoding="utf-8")
    tasks = []

    # 按 ## 分割各图片块
    blocks = re.split(r'\n## ', content)

    for block in blocks[1:]:  # 跳过文件头
        lines = block.strip().split('\n')
        name = lines[0].strip()

        # 提取 Prompt 代码块内容（```...```）
        prompt_match = re.search(r'```\n(.*?)\n```', block, re.DOTALL)
        if not prompt_match:
            print(f"⚠️  跳过「{name}」：未找到 Prompt 代码块")
            continue

        # 取最后一个代码块（通常是英文 Prompt，排除图内文字代码块）
        all_code_blocks = re.findall(r'```\n(.*?)\n```', block, re.DOTALL)
        # 找英文 prompt：选最长的代码块（中文图内文字通常较短）
        prompt = max(all_code_blocks, key=len).strip()

        # 过滤掉明显是"图内文字"的块（含中文）
        chinese_ratio = sum(1 for c in prompt if '\u4e00' <= c <= '\u9fff') / max(len(prompt), 1)
        if chinese_ratio > 0.1:
            # 如果最长块也含大量中文，取最后一个英文块
            for code in reversed(all_code_blocks):
                cr = sum(1 for c in code if '\u4e00' <= c <= '\u9fff') / max(len(code), 1)
                if cr < 0.1:
                    prompt = code.strip()
                    break

        if prompt:
            tasks.append({"name": name, "prompt": prompt})
            print(f"✅ 解析成功：{name} ({len(prompt)} 字符)")

    return tasks


# ─── 提交单个生成任务 ─────────────────────────────────────────────
async def submit_task(session: aiohttp.ClientSession, task: dict) -> dict:
    """提交生成任务，返回任务ID"""
    payload = {
        "model": MODEL,
        "prompt": task["prompt"],
        "aspectRatio": ASPECT_RATIO,
        "webHook": "-1"  # 立即返回任务ID，不等待
    }
    try:
        async with session.post(ENDPOINT, headers=HEADERS, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json()
            task_id = data.get("id") or data.get("taskId")
            if task_id:
                print(f"  📤 已提交「{task['name']}」→ 任务ID: {task_id}")
                return {"name": task["name"], "task_id": task_id, "status": "pending"}
            else:
                print(f"  ❌ 提交失败「{task['name']}」: {data}")
                return {"name": task["name"], "task_id": None, "status": "failed", "error": str(data)}
    except Exception as e:
        print(f"  ❌ 提交异常「{task['name']}」: {e}")
        return {"name": task["name"], "task_id": None, "status": "failed", "error": str(e)}


# ─── 轮询任务状态 ─────────────────────────────────────────────────
async def poll_task(session: aiohttp.ClientSession, task_result: dict) -> dict:
    """轮询直到任务完成，返回图片URL"""
    if not task_result.get("task_id"):
        return task_result

    task_id = task_result["task_id"]
    name = task_result["name"]
    elapsed = 0

    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        try:
            url = f"{BASE_URL}/v1/draw/result/{task_id}"
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                status = data.get("status", "")
                progress = data.get("progress", 0)

                print(f"  ⏳ 「{name}」进度: {progress}% ({elapsed}s)")

                if status == "succeeded":
                    results = data.get("results", [])
                    if results:
                        img_url = results[0].get("url")
                        print(f"  ✅ 「{name}」完成！")
                        return {**task_result, "status": "succeeded", "img_url": img_url}

                elif status == "failed":
                    print(f"  ❌ 「{name}」生成失败")
                    return {**task_result, "status": "failed"}

        except Exception as e:
            print(f"  ⚠️  轮询异常「{name}」: {e}")

    print(f"  ⏰ 「{name}」超时（{POLL_TIMEOUT}s）")
    return {**task_result, "status": "timeout"}


# ─── 下载图片 ─────────────────────────────────────────────────────
async def download_image(session: aiohttp.ClientSession, task_result: dict, output_dir: Path) -> str:
    """下载图片到本地，返回文件路径"""
    if task_result.get("status") != "succeeded":
        return None

    img_url = task_result.get("img_url")
    name = task_result["name"]

    # 生成安全的文件名
    safe_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', name)
    idx = task_result.get("index", 0)
    filename = f"{idx:02d}_{safe_name}.png"
    filepath = output_dir / filename

    try:
        async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                filepath.write_bytes(await resp.read())
                print(f"  💾 已保存：{filename}")
                return str(filepath)
            else:
                print(f"  ❌ 下载失败「{name}」: HTTP {resp.status}")
                return None
    except Exception as e:
        print(f"  ❌ 下载异常「{name}」: {e}")
        return None


# ─── 主流程 ───────────────────────────────────────────────────────
async def main(md_path: str):
    print(f"\n{'='*60}")
    print(f"🍌 Nano Banana Pro 批量图片生成器")
    print(f"{'='*60}")
    print(f"📄 读取文件：{md_path}")

    # 1. 解析 prompts.md
    tasks = parse_prompts_md(md_path)
    if not tasks:
        print("❌ 未解析到任何任务，请检查 prompts.md 格式")
        return

    print(f"\n📋 共解析 {len(tasks)} 个图片任务")

    # 2. 创建输出目录（与 prompts.md 同目录）
    md_dir = Path(md_path).parent
    timestamp = datetime.now().strftime("%H%M%S")
    output_dir = md_dir / f"images_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录：{output_dir}")

    # 3. 批量提交任务（限制并发）
    print(f"\n🚀 开始提交任务（并发数: {MAX_CONCURRENT}）...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    submitted = []

    async with aiohttp.ClientSession() as session:
        # 提交阶段
        async def submit_with_sem(task):
            async with semaphore:
                return await submit_task(session, task)

        submitted = await asyncio.gather(*[submit_with_sem(t) for t in tasks])

        # 加入序号（用于文件命名）
        for i, result in enumerate(submitted):
            result["index"] = i

        # 4. 轮询所有任务
        print(f"\n⏳ 等待生成完成...")
        completed = await asyncio.gather(*[poll_task(session, r) for r in submitted])

        # 5. 下载所有图片
        print(f"\n💾 开始下载图片...")
        saved_files = await asyncio.gather(*[download_image(session, r, output_dir) for r in completed])

    # 6. 生成汇总报告
    success = [f for f in saved_files if f]
    failed = [r["name"] for r, f in zip(completed, saved_files) if not f]

    print(f"\n{'='*60}")
    print(f"✅ 生成完成！")
    print(f"   成功：{len(success)}/{len(tasks)} 张")
    if failed:
        print(f"   失败：{', '.join(failed)}")
    print(f"   保存位置：{output_dir}")
    print(f"{'='*60}\n")

    # 保存汇总 JSON
    report = {
        "generated_at": datetime.now().isoformat(),
        "source_file": md_path,
        "output_dir": str(output_dir),
        "total": len(tasks),
        "success": len(success),
        "failed": len(failed),
        "files": success
    }
    report_path = output_dir / "generation_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"📊 报告已保存：{report_path}")

    return output_dir


# ─── 入口 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 nb_batch_generate.py <prompts.md路径>")
        print("示例：python3 nb_batch_generate.py /data/workspace/AIContentFlow/outputs/archive/2026-03-07/龙虾之父_小红书图片prompts.md")
        sys.exit(1)

    md_file = sys.argv[1]
    if not Path(md_file).exists():
        print(f"❌ 文件不存在：{md_file}")
        sys.exit(1)

    asyncio.run(main(md_file))
