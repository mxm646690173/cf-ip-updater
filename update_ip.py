#!/usr/bin/env python3
"""
CF优选IP自动更新脚本 (Playwright/Curl版)
1. 每次运行前清空 Worker 中所有优选IP
2. 从 cf.junzhen.qzz.io 获取数据
3. 筛选: HK/KR 地区且速度 > 10M
4. 批量通过 cfnew API 添加 (添加前先清空)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

# ============ 配置 ============
SOURCE_URL = "https://cf.junzhen.qzz.io/full_ips_bj.txt"
CFNEW_URL = os.environ.get("CFNEW_URL", "")

# 模拟浏览器的 Headers，防止被 WAF 拦截 (403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Referer": CFNEW_URL.split('/api/')[0] + '/',
    "Content-Type": "application/json"
}

def fetch_data():
    req = urllib.request.Request(SOURCE_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clear_ips():
    print("🧹 正在清空旧 IP...")
    req = urllib.request.Request(
        CFNEW_URL, 
        data=json.dumps({"all": True}).encode(), 
        headers=HEADERS, 
        method="DELETE"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"✅ 已清空: {resp.read().decode()}")

def bulk_add_ips(ips_to_add):
    print(f"🚀 正在批量添加 {len(ips_to_add)} 个 IP...")
    payload = json.dumps(ips_to_add).encode()
    req = urllib.request.Request(
        CFNEW_URL, 
        data=payload, 
        headers=HEADERS, 
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"✅ 批量添加成功: {resp.read().decode()}")

def main():
    if not CFNEW_URL:
        print("❌ 错误: 未设置 CFNEW_URL")
        sys.exit(1)

    # 1. 清空旧数据
    try:
        clear_ips()
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        sys.exit(1)

    # 2. 获取并筛选数据
    raw_text = fetch_data()
    filtered_ips = []
    counters = {} # 用于存储各地区序号
    pattern = re.compile(r"(?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)#(?P<region>[A-Z]+)\s+\[(?P<speed>\d+)M\]")
    
    for line in raw_text.splitlines():
        match = pattern.search(line)
        if match:
            data = match.groupdict()
            if data['region'] in ['HK', 'KR'] and int(data['speed']) > 10:
                region = data['region']
                counters[region] = counters.get(region, 0) + 1
                filtered_ips.append({
                    "ip": data['ip'],
                    "port": int(data['port']),
                    "name": f"{region}-{counters[region]}-{data['speed']}M"
                })
    
    if not filtered_ips:
        print("⚠️ 未找到符合条件的 IP")
        return

    # 3. 批量添加
    try:
        bulk_add_ips(filtered_ips)
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
