#!/usr/bin/env python3
"""
CF优选IP自动更新脚本
从 api.uouin.com/cloudflare.html 获取电信第一条优选IP，
推送到 cfnew API (byJoey/cfnew)
"""

import json
import os
import re
import ssl
import sys
import urllib.request
import urllib.error

# ============ 配置 ============
SOURCE_URL = "https://api.uouin.com/cloudflare.html"
# 从环境变量读取 cfnew API 地址，格式: https://your-worker.workers.dev/{UUID或自定义路径}
CFNEW_API_BASE = os.environ.get("CFNEW_API_BASE", "")
# 如果上面为空，则从 CFNEW_URL 环境变量读取完整API地址
CFNEW_URL = os.environ.get("CFNEW_URL", "")
PORT = int(os.environ.get("CFNEW_PORT", "443"))
NAME = os.environ.get("CFNEW_NAME", "ip优选")
# ==============================


def fetch_html(url: str) -> str:
    """获取网页HTML内容"""
    # 创建宽松的SSL上下文，兼容更多服务器配置
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_first_telecom_ip(html: str) -> str | None:
    """
    从HTML中提取电信线路的第一条优选IP
    """
    # 找到所有表格行
    rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)
    for row in rows:
        # 查找包含"电信"的行
        if "电信" in row:
            # 提取IP地址
            ips = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", row)
            if ips:
                return ips[0]
    return None


def push_to_cfnew(ip: str, port: int, name: str) -> dict:
    """
    通过 cfnew API 推送优选IP
    """
    # 创建宽松的SSL上下文
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 构造API地址
    if CFNEW_URL:
        api_url = CFNEW_URL
    elif CFNEW_API_BASE:
        api_url = f"{CFNEW_API_BASE.rstrip('/')}/api/preferred-ips"
    else:
        print("❌ 错误: 未设置 CFNEW_API_BASE 或 CFNEW_URL 环境变量")
        sys.exit(1)

    payload = json.dumps({"ip": ip, "port": port, "name": name}).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cf-ip-updater/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            print(f"✅ 推送成功! 状态码: {resp.status}")
            print(f"   响应: {body[:500]}")
            return {"status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ 推送失败! 状态码: {e.code}")
        print(f"   响应: {body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e.reason}")
        sys.exit(1)


def main():
    print("=" * 50)
    print("CF优选IP自动更新脚本")
    print("=" * 50)

    # 1. 获取网页
    print(f"\n📡 正在获取: {SOURCE_URL}")
    html = fetch_html(SOURCE_URL)
    print(f"   已获取 HTML ({len(html)} 字节)")

    # 2. 提取电信优选IP
    print("\n🔍 正在提取电信线路第一条优选IP...")
    ip = extract_first_telecom_ip(html)
    if not ip:
        print("❌ 未找到电信线路的IP记录")
        sys.exit(1)
    print(f"   ✅ 找到电信优选IP: {ip}")

    # 3. 推送到cfnew
    print(f"\n📤 正在推送到 cfnew API...")
    print(f"   IP: {ip}")
    print(f"   Port: {PORT}")
    print(f"   Name: {NAME}")
    push_to_cfnew(ip, PORT, NAME)

    print("\n" + "=" * 50)
    print("✅ 完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()