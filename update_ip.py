#!/usr/bin/env python3
"""
CF优选IP自动更新脚本 (Playwright版)
使用无头浏览器访问 api.uouin.com/cloudflare.html，
等待数据刷新后提取电信线路第一条优选IP，
推送到 cfnew API (byJoey/cfnew)
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

# ============ 配置 ============
SOURCE_URL = "https://api.uouin.com/cloudflare.html"
# 从环境变量读取 cfnew API 完整地址
CFNEW_URL = os.environ.get("CFNEW_URL", "")
PORT = int(os.environ.get("CFNEW_PORT", "443"))
NAME = os.environ.get("CFNEW_NAME", "ip优选")
# 等待页面JS刷新数据的最大时间（秒）
WAIT_TIMEOUT = int(os.environ.get("WAIT_TIMEOUT", "90"))
# ==============================


def extract_first_telecom_ip(html: str) -> str | None:
    """
    从HTML中提取电信线路的第一条优选IP
    """
    rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)
    for row in rows:
        if "电信" in row:
            ips = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", row)
            if ips:
                return ips[0]
    return None


def push_to_cfnew(ip: str, port: int, name: str) -> dict:
    """通过 cfnew API 推送优选IP"""
    if not CFNEW_URL:
        print("❌ 错误: 未设置 CFNEW_URL 环境变量")
        sys.exit(1)

    payload = json.dumps({"ip": ip, "port": port, "name": name}).encode("utf-8")

    req = urllib.request.Request(
        CFNEW_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cf-ip-updater/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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
    print("CF优选IP自动更新脚本 (Playwright版)")
    print("=" * 50)

    # 1. 使用 Playwright 无头浏览器访问页面
    print(f"\n🌐 正在启动无头浏览器访问: {SOURCE_URL}")
    print(f"   等待数据刷新（最长 {WAIT_TIMEOUT} 秒）...")

    html = ""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # 启动无头 Chromium
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            # 访问页面
            page.goto(SOURCE_URL, wait_until="networkidle", timeout=30000)

            # 等待数据刷新：轮询检查表格中的日期是否变化
            # 初始数据是旧数据（2024/04/09），等待JS刷新后日期会变化
            start_time = time.time()
            refreshed = False

            while time.time() - start_time < WAIT_TIMEOUT:
                # 获取当前页面HTML
                html = page.content()

                # 找到所有电信IP
                rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)
                telecom_rows = [r for r in rows if "电信" in r]

                if telecom_rows:
                    # 检查日期是否已更新（不是那个旧日期）
                    dates = re.findall(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", telecom_rows[0])
                    if dates and "2024/04/09" not in dates[0]:
                        print(f"   ✅ 数据已刷新! 日期: {dates[0]}")
                        refreshed = True
                        break
                    else:
                        remaining = int(WAIT_TIMEOUT - (time.time() - start_time))
                        print(f"   ⏳ 数据仍为旧数据，继续等待... (剩余 {remaining} 秒)")

                # 等待5秒再检查
                time.sleep(5)

            if not refreshed:
                # 超时，使用当前页面数据
                print(f"   ⚠️ 等待超时 {WAIT_TIMEOUT} 秒，使用当前页面数据")
                html = page.content()

            browser.close()

    except ImportError:
        print("❌ 未安装 Playwright。请执行: pip install playwright && python -m playwright install chromium")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 浏览器操作失败: {e}")
        sys.exit(1)

    print(f"   已获取页面 HTML ({len(html)} 字节)")

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