#!/usr/bin/env python3
"""
CF优选IP自动更新脚本 (Playwright/Curl版)
1. 每日运行清空 Worker 中所有优选IP
2. 从 cf.junzhen.qzz.io 获取数据
3. 筛选: HK/KR 地区且速度 > 10M
4. 批量通过 cfnew API 添加
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import date

# ============ 配置 ============
SOURCE_URL = "https://cf.junzhen.qzz.io/full_ips_bj.txt"
CFNEW_URL = os.environ.get("CFNEW_URL", "")
STATE_FILE = "state.json"
# =============================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_date": "", "count": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}
    req = urllib.request.Request(SOURCE_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clear_ips():
    print("🧹 正在清空旧 IP...")
    req = urllib.request.Request(CFNEW_URL, data=json.dumps({"all": True}).encode(), headers={"Content-Type": "application/json"}, method="DELETE")
    urllib.request.urlopen(req, timeout=30)
    print("✅ 已清空")

def bulk_add_ips(ips_to_add):
    print(f"🚀 正在批量添加 {len(ips_to_add)} 个 IP...")
    payload = json.dumps(ips_to_add).encode()
    req = urllib.request.Request(CFNEW_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=30)
    print("✅ 批量添加成功")

def main():
    if not CFNEW_URL:
        print("❌ 错误: 未设置 CFNEW_URL")
        sys.exit(1)

    # 1. 状态管理
    state = load_state()
    today = str(date.today())
    if state["last_date"] == today:
        state["count"] += 1
    else:
        state["last_date"] = today
        state["count"] = 1
    
    current_name = f"{today}-{state['count']}"
    
    # 2. 清空旧数据
    try:
        clear_ips()
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        sys.exit(1)

    # 3. 获取并筛选数据
    raw_text = fetch_data()
    filtered_ips = []
    # 格式: 152.67.210.234:443#KR [12M]
    pattern = re.compile(r"(?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)#(?P<region>[A-Z]+)\s+\[(?P<speed>\d+)M\]")
    
    for line in raw_text.splitlines():
        match = pattern.search(line)
        if match:
            data = match.groupdict()
            if data['region'] in ['HK', 'KR'] and int(data['speed']) > 10:
                filtered_ips.append({
                    "ip": data['ip'],
                    "port": int(data['port']),
                    "name": current_name
                })
    
    if not filtered_ips:
        print("⚠️ 未找到符合条件的 IP")
        return

    # 4. 批量添加
    try:
        bulk_add_ips(filtered_ips)
        save_state(state)
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
