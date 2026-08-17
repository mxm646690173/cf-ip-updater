#!/usr/bin/env python3
"""
CF优选IP自动更新脚本 (Playwright版)
使用无头浏览器访问 api.uouin.com/cloudflare.html，
等待数据刷新后提取电信线路第一条优选IP，
推送到 cfnew API (byJoey/cfnew)

逻辑：
- 每天第1次运行：先清空所有优选IP，再添加新IP
- 同天后续运行：只添加新IP，不再清空
- name 格式：YYYY-MM-DD-N（日期-第N次获取）
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import date

# ============ 配置 ============
SOURCE_URL = "https://api.uouin.com/cloudflare.html"
# 从环境变量读取 cfnew API 完整地址
CFNEW_URL = os.environ.get("CFNEW_URL", "")
PORT = int(os.environ.get("CFNEW_PORT", "443"))
# 等待页面JS刷新数据的最大时间（秒）
WAIT_TIMEOUT = int(os.environ.get("WAIT_TIMEOUT", "90"))
# 状态文件路径
STATE_FILE = "state.json"
# ==============================


def load_state() -> dict:
    """读取运行状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"date": "", "count": 0}


def save_state(state: dict):
    """保存运行状态"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"   📝 状态已保存: date={state['date']}, count={state['count']}")


def delete_all_ips():
    """清空 cfnew 中的所有优选IP"""
    if not CFNEW_URL:
        print("❌ 错误: 未设置 CFNEW_URL 环境变量")
        sys.exit(1)

    # DELETE 请求的 URL 与 POST 相同
    req = urllib.request.Request(
        CFNEW_URL,
        data=json.dumps({"all": True}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "cf-ip-updater/1.0",
        },
        method="DELETE",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            print(f"   ✅ 已清空所有优选IP! 状态码: {resp.status}")
            print(f"     响应: {body[:300]}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"   ⚠️ 清空失败! 状态码: {e.code} - {body[:200]}")
        return False
    except urllib.error.URLError as e:
        print(f"   ⚠️ 清空网络错误: {e.reason}")
        return False


def extract_first_telecom_ip(html: str) -> str | None:
    """从HTML中提取电信线路的第一条优选IP"""
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
            print(f"   ✅ 推送成功! 状态码: {resp.status}")
            print(f"     响应: {body[:300]}")
            return {"status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"   ❌ 推送失败! 状态码: {e.code}")
        print(f"     响应: {body[:300]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"   ❌ 网络错误: {e.reason}")
        sys.exit(1)


def fetch_ip_with_playwright() -> str:
    """使用Playwright无头浏览器获取页面，等待数据刷新后返回HTML"""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.goto(SOURCE_URL, wait_until="networkidle", timeout=30000)

            # 轮询等待数据刷新
            start_time = time.time()
            html = ""

            while time.time() - start_time < WAIT_TIMEOUT:
                html = page.content()
                rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)
                telecom_rows = [r for r in rows if "电信" in r]

                if telecom_rows:
                    dates = re.findall(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", telecom_rows[0])
                    if dates and "2024/04/09" not in dates[0]:
                        print(f"   ✅ 数据已刷新! 日期: {dates[0]}")
                        break
                    else:
                        remaining = int(WAIT_TIMEOUT - (time.time() - start_time))
                        print(f"   ⏳ 数据仍为旧数据，继续等待... (剩余 {remaining} 秒)")

                time.sleep(5)

            browser.close()
            return html

    except ImportError:
        print("❌ 未安装 Playwright。请执行: pip install playwright && python -m playwright install chromium")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 浏览器操作失败: {e}")
        sys.exit(1)


def main():
    print("=" * 50)
    print("CF优选IP自动更新脚本 (Playwright版)")
    print("=" * 50)

    # 1. 读取运行状态，判断是否当天第一次运行
    today = date.today().isoformat()  # 格式: YYYY-MM-DD
    state = load_state()
    is_first_run_today = (state.get("date") != today)

    if is_first_run_today:
        state["date"] = today
        state["count"] = 0

    # 递增计数
    state["count"] += 1
    run_count = state["count"]
    node_name = f"{today}-{run_count}"

    print(f"\n📅 当前日期: {today}")
    print(f"📊 今日第 {run_count} 次运行")
    print(f"📛 节点名称: {node_name}")

    # 2. 如果是当天第一次运行，先清空所有IP
    if is_first_run_today:
        print(f"\n🗑️  当天第一次运行，正在清空所有优选IP...")
        delete_all_ips()
    else:
        print(f"\n⏭️  非当天第一次运行，跳过清空操作")

    # 3. 使用 Playwright 获取页面数据
    print(f"\n🌐 正在启动无头浏览器访问: {SOURCE_URL}")
    print(f"   等待数据刷新（最长 {WAIT_TIMEOUT} 秒）...")
    html = fetch_ip_with_playwright()
    print(f"   已获取页面 HTML ({len(html)} 字节)")

    # 4. 提取电信优选IP
    print("\n🔍 正在提取电信线路第一条优选IP...")
    ip = extract_first_telecom_ip(html)
    if not ip:
        print("❌ 未找到电信线路的IP记录")
        sys.exit(1)
    print(f"   ✅ 找到电信优选IP: {ip}")

    # 5. 推送到 cfnew
    print(f"\n📤 正在推送到 cfnew API...")
    print(f"   IP: {ip}")
    print(f"   Port: {PORT}")
    print(f"   Name: {node_name}")
    push_to_cfnew(ip, PORT, node_name)

    # 6. 保存状态
    save_state(state)

    print("\n" + "=" * 50)
    print("✅ 完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()