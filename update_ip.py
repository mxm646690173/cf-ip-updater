#!/usr/bin/env python3
"""
CF优选IP自动更新脚本
1. 从 cf.junzhen.qzz.io 获取数据
2. 筛选: HK/KR 地区且速度 > 10M
3. 每次运行先清空所有优选IP，再批量添加
4. 节点命名: 地区-序号-速度 (如 HK-1-12M)
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
# =============================


def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}
    req = urllib.request.Request(SOURCE_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def clear_ips():
    print("🧹 正在清空旧 IP...")
    req = urllib.request.Request(
        CFNEW_URL,
        data=json.dumps({"all": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="DELETE",
    )
    urllib.request.urlopen(req, timeout=30)
    print("✅ 已清空")


def bulk_add_ips(ips_to_add):
    print(f"🚀 正在批量添加 {len(ips_to_add)} 个 IP...")
    payload = json.dumps(ips_to_add).encode()
    req = urllib.request.Request(
        CFNEW_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30)
    print("✅ 批量添加成功")


def main():
    if not CFNEW_URL:
        print("❌ 错误: 未设置 CFNEW_URL")
        sys.exit(1)

    # 1. 获取并筛选数据
    print(f"🌐 正在获取数据: {SOURCE_URL}")
    raw_text = fetch_data()
    print(f"   已获取 {len(raw_text.splitlines())} 行原始数据")

    filtered_ips = []
    # 格式: 152.67.210.234:443#KR [12M]
    pattern = re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+):(?P<port>\d+)#(?P<region>[A-Z]+)\s+\[(?P<speed>\d+)M\]"
    )
    # 按地区分组计数
    region_counter = {}

    for line in raw_text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        data = match.groupdict()
        region = data["region"]
        speed = int(data["speed"])

        # 筛选: HK/KR 地区且速度 > 10M
        if region not in ("HK", "KR") or speed <= 10:
            continue

        # 地区内序号从1开始
        region_counter[region] = region_counter.get(region, 0) + 1
        name = f"{region}-{region_counter[region]}-{data['speed']}M"

        filtered_ips.append({
            "ip": data["ip"],
            "port": int(data["port"]),
            "name": name,
        })

    if not filtered_ips:
        print("⚠️ 未找到符合条件的 IP (HK/KR 且速度 > 10M)")
        sys.exit(1)

    hk_count = region_counter.get("HK", 0)
    kr_count = region_counter.get("KR", 0)
    print(f"   ✅ 筛选出 {len(filtered_ips)} 个节点: HK={hk_count}, KR={kr_count}")
    for item in filtered_ips:
        print(f"      {item['name']}: {item['ip']}:{item['port']}")

    # 2. 清空旧数据
    try:
        clear_ips()
    except Exception as e:
        print(f"❌ 清空失败: {e}")
        sys.exit(1)

    # 3. 批量添加
    try:
        bulk_add_ips(filtered_ips)
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        sys.exit(1)

    print("✅ 全部完成")


if __name__ == "__main__":
    main()