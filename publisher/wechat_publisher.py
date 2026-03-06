#!/usr/bin/env python3
"""
AIContentFlow - 微信公众号发布模块
功能：
  1. 将 Markdown 文件通过 mdnice_formatter.js 排版为微信 HTML
  2. 调用微信公众号草稿接口上传为草稿
  3. 可选：一键发布（需公众号开通发布权限）

用法：
  # 排版 + 上传草稿
  python3 wechat_publisher.py --file /path/to/article.md

  # 指定主题
  python3 wechat_publisher.py --file /path/to/article.md --theme normal

  # 仅排版，不上传
  python3 wechat_publisher.py --file /path/to/article.md --format-only

  # 上传草稿后直接发布
  python3 wechat_publisher.py --file /path/to/article.md --publish

作者：AIContentFlow
版本：1.0.0
"""

import os
import re
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

try:
    import requests as _requests
    _USE_REQUESTS = True
except ImportError:
    _USE_REQUESTS = False

# 自动加载 .env
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

# ============================================================================
# 配置
# ============================================================================

WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_APPSECRET = os.getenv("WECHAT_APPSECRET", "")

# mdnice_formatter.js 的路径
FORMATTER_JS = Path(__file__).parent / "mdnice_formatter.js"

# access_token 本地缓存文件
TOKEN_CACHE_FILE = Path(__file__).parent.parent / ".wechat_token_cache.json"

# ============================================================================
# 微信 access_token 管理
# ============================================================================

def get_access_token() -> str:
    """获取微信 access_token（带本地缓存，有效期内不重复请求）"""
    # 读缓存
    if TOKEN_CACHE_FILE.exists():
        try:
            with open(TOKEN_CACHE_FILE) as f:
                cache = json.load(f)
            if cache.get("expires_at", 0) > time.time() + 60:
                return cache["access_token"]
        except Exception:
            pass

    if not WECHAT_APPID or not WECHAT_APPSECRET:
        print("  ❌ 未配置 WECHAT_APPID 或 WECHAT_APPSECRET，请检查 .env")
        sys.exit(1)

    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential"
        f"&appid={WECHAT_APPID}"
        f"&secret={WECHAT_APPSECRET}"
    )

    print("  🔑 获取微信 access_token...")
    resp = _wx_get(url)
    if "access_token" not in resp:
        print(f"  ❌ 获取 access_token 失败: {resp}")
        sys.exit(1)

    token = resp["access_token"]
    expires_in = resp.get("expires_in", 7200)

    # 写缓存
    try:
        with open(TOKEN_CACHE_FILE, "w") as f:
            json.dump({
                "access_token": token,
                "expires_at": time.time() + expires_in,
            }, f)
    except Exception:
        pass

    print(f"  ✅ access_token 已获取（有效期 {expires_in}s）")
    return token


def _wx_get(url: str) -> dict:
    """发送 GET 请求"""
    if _USE_REQUESTS:
        resp = _requests.get(url, timeout=20)
        return resp.json()
    else:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read())


def _wx_post(url: str, data: dict = None, files: dict = None) -> dict:
    """发送 POST 请求"""
    if _USE_REQUESTS:
        if files:
            resp = _requests.post(url, files=files, timeout=30)
        else:
            resp = _requests.post(url, json=data, timeout=30)
        return resp.json()
    else:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())


# ============================================================================
# Step 1：mdnice 排版
# ============================================================================

def format_with_mdnice(md_file: str, theme: str = "normal") -> str:
    """
    调用 mdnice_formatter.js 将 Markdown 转换为微信 HTML
    返回输出的 HTML 文件路径
    """
    if not FORMATTER_JS.exists():
        print(f"  ❌ 排版脚本不存在: {FORMATTER_JS}")
        sys.exit(1)

    md_path = Path(md_file).resolve()
    html_path = md_path.parent / (md_path.stem + "_wechat.html")

    print(f"  🎨 正在排版（主题: {theme}）...")
    try:
        result = subprocess.run(
            ["node", str(FORMATTER_JS), str(md_path), str(html_path), f"--theme={theme}"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  ❌ 排版失败:\n{result.stderr}")
            sys.exit(1)

        # stderr 是日志，stdout 是输出文件路径
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                print(f"     {line}")

        output_path = result.stdout.strip() or str(html_path)
        print(f"  ✅ 排版完成: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        print("  ❌ 排版超时（>60s）")
        sys.exit(1)
    except FileNotFoundError:
        print("  ❌ 未找到 node 命令，请确认 Node.js 已安装")
        sys.exit(1)


def read_html(html_file: str) -> str:
    """读取 HTML 文件内容"""
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# Step 2：上传图片到微信素材库（封面图）
# ============================================================================

def upload_thumb(image_path: str, access_token: str) -> str:
    """
    上传封面图到微信永久素材库，返回 media_id
    支持 jpg/png，建议尺寸 900×500px
    """
    if not image_path or not os.path.exists(image_path):
        print("  ⚠️  未提供封面图，将使用默认占位图")
        return None

    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    print(f"  🖼️  上传封面图: {image_path}")

    if _USE_REQUESTS:
        with open(image_path, "rb") as f:
            resp = _requests.post(url, files={"media": f}, timeout=30)
        result = resp.json()
    else:
        print("  ⚠️  上传封面图需要 requests 库，跳过")
        return None

    if "media_id" in result:
        media_id = result["media_id"]
        print(f"  ✅ 封面图上传成功，media_id: {media_id}")
        return media_id
    else:
        print(f"  ⚠️  封面图上传失败: {result}，将跳过封面")
        return None


# ============================================================================
# Step 3：上传草稿到微信公众号
# ============================================================================

def upload_draft(
    title: str,
    html_content: str,
    access_token: str,
    thumb_media_id: str = None,
    digest: str = None,
    author: str = None,
) -> dict:
    """
    上传文章草稿到微信公众号草稿箱
    返回 media_id（草稿ID）
    """
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

    # 构建文章对象
    article = {
        "title": title,
        "content": html_content,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }

    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
    if digest:
        article["digest"] = digest[:120]  # 摘要最多120字
    if author:
        article["author"] = author

    payload = {"articles": [article]}

    print(f"  📤 上传草稿到微信公众号...")
    print(f"     标题: {title}")
    print(f"     内容长度: {len(html_content)} 字符")

    result = _wx_post(url, payload)

    if result.get("errcode", 0) != 0:
        errcode = result.get("errcode")
        errmsg = result.get("errmsg", "未知错误")
        print(f"  ❌ 上传失败 (errcode={errcode}): {errmsg}")
        _print_errcode_hint(errcode)
        return None

    media_id = result.get("media_id")
    print(f"  ✅ 草稿上传成功！")
    print(f"  📋 草稿 media_id: {media_id}")
    print(f"  🔗 请前往公众号后台 → 草稿箱 查看")
    return {"media_id": media_id}


def _print_errcode_hint(errcode: int):
    """打印常见错误码提示"""
    hints = {
        40001: "access_token 无效，请检查 WECHAT_APPID / WECHAT_APPSECRET",
        40003: "不合法的 OpenID",
        45009: "接口调用超过限制（每天有次数限制）",
        48001: "API 功能未授权，请确认公众号已开通相关权限",
        40097: "参数错误，请检查文章内容格式",
    }
    if errcode in hints:
        print(f"  💡 提示: {hints[errcode]}")


# ============================================================================
# Step 4：发布草稿（可选）
# ============================================================================

def publish_draft(media_id: str, access_token: str) -> bool:
    """
    将草稿发布为正式文章
    注意：需要公众号开通「发布」权限（认证服务号才有）
    """
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
    payload = {"media_id": media_id}

    print(f"  🚀 正在发布文章...")
    result = _wx_post(url, payload)

    if result.get("errcode", 0) != 0:
        errcode = result.get("errcode")
        errmsg = result.get("errmsg", "未知错误")
        print(f"  ❌ 发布失败 (errcode={errcode}): {errmsg}")
        if errcode == 48001:
            print("  💡 提示: 自动发布需要认证服务号权限，订阅号请在后台手动发布")
        return False

    publish_id = result.get("publish_id")
    print(f"  ✅ 发布成功！publish_id: {publish_id}")
    return True


# ============================================================================
# 工具函数
# ============================================================================

def extract_title(md_content: str, filename: str) -> str:
    """从 Markdown 内容提取标题"""
    m = re.match(r"^# (.+)", md_content.strip())
    if m:
        return m.group(1).strip()
    return Path(filename).stem


def extract_digest(md_content: str, max_len: int = 100) -> str:
    """提取文章摘要（第一段正文）"""
    lines = md_content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('!') and len(line) > 20:
            # 去除 Markdown 格式
            clean = re.sub(r'\*+|`|~~|\[([^\]]+)\]\([^)]+\)', r'\1', line)
            return clean[:max_len]
    return ""


# ============================================================================
# 主流程
# ============================================================================

def run(args):
    md_file = args.file
    theme = args.theme
    format_only = args.format_only
    do_publish = args.publish
    thumb_image = args.thumb
    author = args.author

    print(f"\n{'='*60}")
    print(f"  AIContentFlow - 微信公众号发布")
    print(f"{'='*60}")
    print(f"  文件: {md_file}")
    print(f"  主题: {theme}")
    print()

    # 读取 Markdown
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    title = extract_title(md_content, md_file)
    digest = extract_digest(md_content)
    print(f"  📝 标题: {title}")

    # Step 1: 排版
    print("\n📐 步骤 1/3：mdnice 排版...")
    html_file = format_with_mdnice(md_file, theme)
    html_content = read_html(html_file)

    if format_only:
        print(f"\n{'='*60}")
        print(f"  ✅ 排版完成（仅排版模式）")
        print(f"  📄 HTML 文件: {html_file}")
        print(f"{'='*60}\n")
        return

    # Step 2: 获取 access_token
    print("\n🔑 步骤 2/3：获取微信授权...")
    access_token = get_access_token()

    # 上传封面图（可选）
    thumb_media_id = None
    if thumb_image:
        thumb_media_id = upload_thumb(thumb_image, access_token)

    # Step 3: 上传草稿
    print("\n📤 步骤 3/3：上传到微信公众号草稿箱...")
    draft_result = upload_draft(
        title=title,
        html_content=html_content,
        access_token=access_token,
        thumb_media_id=thumb_media_id,
        digest=digest,
        author=author,
    )

    if not draft_result:
        print("\n❌ 上传失败，中止")
        sys.exit(1)

    media_id = draft_result["media_id"]

    # 可选：直接发布
    if do_publish:
        print("\n🚀 发布文章...")
        publish_draft(media_id, access_token)

    print(f"\n{'='*60}")
    print(f"  🎉 完成！")
    print(f"  📄 HTML 文件: {html_file}")
    print(f"  📋 草稿 media_id: {media_id}")
    if not do_publish:
        print(f"  💡 请前往公众号后台 → 草稿箱 预览并手动发布")
        print(f"  💡 或执行以下命令直接发布:")
        print(f"     python3 publisher/wechat_publisher.py --file {md_file} --publish")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="AIContentFlow - 微信公众号发布工具")
    parser.add_argument("--file", "-f", required=True, help="Markdown 文件路径")
    parser.add_argument("--theme", "-t", default="lanqing",
                        choices=["normal", "orangeheart", "purple", "green", "blue", "lanqing"],
                        help="mdnice 主题（默认: lanqing）")
    parser.add_argument("--format-only", action="store_true",
                        help="仅排版，不上传微信")
    parser.add_argument("--publish", action="store_true",
                        help="上传草稿后直接发布（需认证服务号权限）")
    parser.add_argument("--thumb", help="封面图路径（jpg/png，建议 900×500px）")
    parser.add_argument("--author", default="", help="作者名称")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()
