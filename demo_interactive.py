#!/usr/bin/env python3
"""
示範新的互動測試腳本功能

這個腳本會自動執行幾個測試案例來展示：
1. RAG Agent 查詢
2. DATCOM Agent 生成
3. Todo List 追蹤
4. State 流動
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from interactive_test_v2 import DatcomAgentInteractiveTester


def demo():
    """執行示範"""
    print("\n" + "="*70)
    print("🎬 DATCOM Assistant Agent 互動測試 V2 - 功能示範")
    print("="*70)
    print("\n這個示範將展示以下功能：")
    print("1. 流式輸出 - 即時看到每個 node 的執行")
    print("2. Supervisor 決策 - 看到 Supervisor 如何選擇 Worker")
    print("3. Todo List - 追蹤任務進度（如果有實作）")
    print("4. State 快照 - 每次執行後的完整狀態\n")

    input("按 Enter 開始示範...")

    tester = DatcomAgentInteractiveTester()

    # 測試案例 1: RAG Agent 查詢
    print("\n" + "="*70)
    print("📝 測試案例 1: 觸發 RAG Agent")
    print("="*70)
    print("\n提問: '什麼是 FLTCON？'\n")
    input("按 Enter 執行...")

    tester.stream_agent_execution("什麼是 FLTCON？")

    input("\n\n按 Enter 繼續下一個測試...")

    # 測試案例 2: DATCOM Agent 生成
    print("\n" + "="*70)
    print("📝 測試案例 2: 觸發 DATCOM Agent")
    print("="*70)
    print("\n提問: '請生成一個通用飛機的 DATCOM 檔案'\n")
    input("按 Enter 執行...")

    tester.stream_agent_execution("請生成一個通用飛機的 DATCOM 檔案")

    # 顯示最終狀態
    print("\n" + "="*70)
    print("📊 會話總結")
    print("="*70)
    tester.show_status()
    print("\n")
    tester.show_current_state()

    print("\n" + "="*70)
    print("✅ 示範完成！")
    print("="*70)
    print("\n要開始真正的互動會話嗎？")
    choice = input("輸入 'y' 開始互動，或按 Enter 退出: ").strip().lower()

    if choice == 'y':
        print("\n開始互動模式...\n")
        tester.run()
    else:
        print("\n再見！")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\n👋 示範已取消")
    except Exception as e:
        print(f"\n❌ 示範失敗: {e}")
        import traceback
        traceback.print_exc()
