#!/usr/bin/env python3
"""
CF优选IP自动更新脚本
1. 每次运行前清空 Worker 中所有优选IP (带重试机制)
2. 从 cf.junzhen.qzz.io 获取数据 (兼容多种格式)
3. 筛选: HK/KR 地区且速度 > 10M
4. 批量通过 cfnew API 添加
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

# ============ 配置 ============
SOURCE_URL = "https://cf.junzhen.qzz.io/full_ips_bj.txt"
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
    print(f"🧹 正在清空旧 IP (带重试)...")
    body = json.dumps({"all": True}).encode()
    headers = {**HEADERS, "Content-Length": str(len(body))}
    
    for i in range(3):
        try:
            req = urllib.request.Request(API_URL, data=body, headers=headers, method="DELETE")
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"✅ 已清空: {resp.read().decode()}")
                return
        except Exception as e:
            print(f"⚠️ 第 {i+1} 次清空失败: {e}")
            if i < 2: time.sleep(3)
            else: raise e

def bulk_add_ips(ips_to_add):
    print(f"🚀 正在批量添加 {len(ips_to_add)} 个 IP...")
    payload = json.dumps(ips_to_add).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={**HEADERS, "Content-Length": str(len(payload))}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"✅ 批量添加成功: {resp.read().decode()}")

def main():
    if not BASE_URL:
        print("❌ 错误: 未设置 CFNEW_URL")
        sys.exit(1)

    try:
        clear_ips()
    except Exception as e:
        print(f"❌ 最终清空失败: {e}")
        sys.exit(1)

    raw_text = fetch_data()
    filtered_ips = []
    counters = {}
    
    pattern = re.compile(r"(?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)#(?P<region>[A-Z]+)\s+\[(?:.*? )?(?P<speed>\d+)M\]")
    
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
