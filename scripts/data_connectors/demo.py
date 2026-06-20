#!/usr/bin/env python3
"""
Aximora 出海数据采集 — 快速演示
================================
运行: python -m data_connectors.demo

演示所有免费接口的基本调用，确认连通性。
"""

from __future__ import annotations
import json
import sys


def main():
    from .registry import get_registry

    reg = get_registry()

    print("=" * 60)
    print("Aximora 出海数据采集 — 接口连通性测试")
    print("=" * 60)

    # 列出所有连接器
    print("\n📋 已注册连接器:")
    for info in reg.list_connectors():
        key_status = "🔑 需要Key" if info["requires_key"] else "✅ 免费"
        print(f"  - {info['name']:25s} [{info['cost_tier']:10s}] {key_status}")

    # 测试免费接口
    print("\n" + "=" * 60)
    print("测试免费接口")
    print("=" * 60)

    # 1. 汇率
    print("\n--- ExchangeRate API ---")
    er = reg.get("exchange_rate")
    result = er.query(base_currency="USD", target_currencies=["CNY", "VND", "EUR"])
    if result.ok:
        print(f"  USD → CNY: {result.data.get('CNY')}")
        print(f"  USD → VND: {result.data.get('VND')}")
        print(f"  USD → EUR: {result.data.get('EUR')}")
    else:
        print(f"  ❌ Error: {result.error}")

    # 2. World Bank
    print("\n--- World Bank API ---")
    wb = reg.get("world_bank")
    result = wb.query(country="CHN", indicator="NY.GDP.MKTP.CD", date_range="2022:2024")
    if result.ok and result.data:
        for rec in result.data[:3]:
            print(f"  {rec.get('date')}: GDP = ${rec.get('value', 0):,.0f}")
    else:
        print(f"  ❌ Error: {result.error}")

    # 3. UN Comtrade
    print("\n--- UN Comtrade API ---")
    uc = reg.get("un_comtrade")
    result = uc.get_china_exports(hs_code="8471", year="2023")
    if result.ok:
        print(f"  中国计算机(8471)出口记录数: {result.metadata.get('total_records', 0)}")
        if result.data:
            top = sorted(result.data, key=lambda x: x.get("TradeValue", 0), reverse=True)[:3]
            for rec in top:
                partner = rec.get("ptTitle", "Unknown")
                value = rec.get("TradeValue", 0)
                print(f"  → {partner}: ${value:,.0f}")
    else:
        print(f"  ❌ Error: {result.error}")

    print("\n" + "=" * 60)
    print("测试完成。")
    print("=" * 60)


if __name__ == "__main__":
    main()
