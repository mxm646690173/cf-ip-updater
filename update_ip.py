#!/usr/bin/env python3
"""
CF优选IP自动更新脚本
1. 自动拼接 API 路径
2. 每日清空 + 批量添加 (含筛选)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

# ============ 配置 ============
SOURCE_URL = "https://cf.junzhen.qzz.io/full_ips_bj.txt"
# 用户只需配置基础 Worker URL: https://worker.dev/{UUID}
BASE_URL = os.environ.get("CFNEW_URL", "").rstrip('/')
API_URL = f"{BASE_URL}/api/preferred-ips"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/",
    "Content-Type": "application/json"
}

def fetch_data():
    req = urllib.request.Request(SOURCE_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clear_ips():
    print(f"🧹 正在清空旧 IP: {API_URL}")
    req = urllib.request.Request(API_URL, data=json.dumps({"all": True}).encode(), headers=HEADERS, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"✅ 已清空: {resp.read().decode()}")

def bulk_add_ips(ips_to_add):
    print(f"🚀 正在批量添加 {len(ips_to_add)} 个 IP...")
    payload = json.dumps(ips_to_add).encode()
    req = urllib.request.Request(API_URL, data=payload, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"✅ 批量添加成功: {resp.read().decode()}")

def main():
    if not BASE_URL:
        print("❌ 错误: 未设置 CFNEW_URL")
        sys.exit(1)

    try:
        clear_ips()
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        sys.exit(1)

    raw_text = fetch_data()
    filtered_ips = []
    counters = {}
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

    try:
        bulk_add_ips(filtered_ips)
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
