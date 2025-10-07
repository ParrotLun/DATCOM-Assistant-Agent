#!/usr/bin/env python3
"""
DATCOM Assistant Agent 互動測試腳本
允許用戶與 Agent 進行對話並觀察處理流程
"""

import sys
import os
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.dirname(__file__))

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

# 導入我們的組件
from agent.supervisor import app

class DatcomAgentTester:
    """DATCOM Agent 測試器"""
    
    def __init__(self):
        self.app = app
        self.thread_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.conversation_history = []
        
    def print_banner(self):
        """顯示歡迎橫幅"""
        print("=" * 60)
        print("🚁 DATCOM Assistant Agent 互動測試")
        print("=" * 60)
        print("歡迎使用 DATCOM Assistant Agent！")
        print("您可以：")
        print("• 請求生成 DATCOM 檔案")
        print("• 詢問 DATCOM 相關問題")
        print("• 查看 RAG 系統的回應")
        print("• 驗證和修改 DATCOM 設定")
        print("")
        print("指令：")
        print("  /help     - 顯示幫助信息")
        print("  /status   - 顯示當前狀態")
        print("  /history  - 顯示對話歷史")
        print("  /clear    - 清空對話歷史")
        print("  /quit     - 退出程式")
        print("=" * 60)
        print()
    
    def print_help(self):
        """顯示幫助信息"""
        print("\n📚 DATCOM Assistant Agent 使用指南")
        print("-" * 40)
        print("示例對話：")
        print("• '請幫我生成一個戰鬥機的 DATCOM 檔案'")
        print("• '什麼是 DATCOM 的 FLTCON 區段？'")
        print("• '如何設定機翼的幾何參數？'")
        print("• '檢查我的 DATCOM 設定是否正確'")
        print("• '修改馬赫數範圍為 0.3 到 2.0'")
        print()
        print("Agent 功能：")
        print("🤖 Supervisor - 智能任務路由")
        print("📚 RAG Agent - 知識庫查詢")
        print("✈️ DATCOM Agent - 檔案生成與驗證")
        print("-" * 40)
    
    def print_status(self):
        """顯示當前狀態"""
        print(f"\n📊 當前狀態")
        print(f"會話 ID: {self.thread_id}")
        print(f"對話次數: {len(self.conversation_history)}")
        print(f"App 可用: {'✅' if self.app else '❌'}")
    
    def print_history(self):
        """顯示對話歷史"""
        if not self.conversation_history:
            print("\n📝 對話歷史為空")
            return
            
        print(f"\n📝 對話歷史 ({len(self.conversation_history)} 條)")
        print("-" * 40)
        for i, entry in enumerate(self.conversation_history, 1):
            timestamp = entry['timestamp']
            user_msg = entry['user_message']
            agent_response = entry['agent_response']
            
            print(f"{i}. [{timestamp}]")
            print(f"   用戶: {user_msg}")
            print(f"   Agent: {agent_response[:100]}...")
            print()
    
    def clear_history(self):
        """清空對話歷史"""
        self.conversation_history.clear()
        self.thread_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = {"configurable": {"thread_id": self.thread_id}}
        print("✅ 對話歷史已清空，開始新會話")
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """發送消息給 Agent"""
        try:
            print(f"\n🤖 正在處理您的請求...")
            
            # 創建輸入狀態
            input_state = {
                "messages": [HumanMessage(content=message)],
                "todo_list": []
            }
            
            # 執行 Agent
            result = await self.app.ainvoke(input_state, config=self.config)
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "messages": [AIMessage(content=f"抱歉，處理您的請求時發生錯誤: {str(e)}")]
            }
    
    def format_agent_response(self, result: Dict[str, Any]) -> str:
        """格式化 Agent 回應"""
        if "error" in result:
            return f"❌ 錯誤: {result['error']}"
        
        messages = result.get("messages", [])
        if not messages:
            return "⚠️ Agent 沒有回應"
        
        # 獲取最後一條 AI 訊息
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
        if ai_messages:
            return ai_messages[-1].content
        
        return "⚠️ 沒有找到 AI 回應"
    
    def display_detailed_result(self, result: Dict[str, Any]):
        """顯示詳細的處理結果"""
        print("\n" + "="*50)
        print("📊 詳細處理結果")
        print("="*50)
        
        # 顯示狀態信息
        if "todo_list" in result:
            todos = result["todo_list"]
            if todos:
                print(f"📋 任務列表 ({len(todos)} 項):")
                for i, todo in enumerate(todos, 1):
                    status_icon = "✅" if todo.get("status") == "completed" else "⏳"
                    print(f"   {i}. {status_icon} {todo.get('task', 'Unknown task')}")
            else:
                print("📋 無待辦任務")
        
        # 顯示生成的內容
        if "last_successful_datcom" in result and result["last_successful_datcom"]:
            datcom_data = result["last_successful_datcom"]
            print(f"\n✈️ 生成的 DATCOM 資料:")
            if isinstance(datcom_data, dict):
                print(f"   案例 ID: {datcom_data.get('case_id', 'Unknown')}")
                print(f"   單位: {datcom_data.get('units', 'Unknown')}")
                print(f"   組件數量: {len([k for k in datcom_data.keys() if k not in ['case_id', 'units']])}")
            else:
                print(f"   內容長度: {len(str(datcom_data))} 字符")
        
        # 顯示訊息數量
        messages = result.get("messages", [])
        print(f"\n💬 對話訊息: {len(messages)} 條")
        
        print("="*50)
    
    async def run_interactive_session(self):
        """運行互動會話"""
        self.print_banner()
        
        while True:
            try:
                # 獲取用戶輸入
                user_input = input("\n💭 您: ").strip()
                
                if not user_input:
                    continue
                
                # 處理特殊指令
                if user_input.startswith('/'):
                    if user_input == '/help':
                        self.print_help()
                    elif user_input == '/status':
                        self.print_status()
                    elif user_input == '/history':
                        self.print_history()
                    elif user_input == '/clear':
                        self.clear_history()
                    elif user_input == '/quit':
                        print("👋 再見！感謝使用 DATCOM Assistant Agent")
                        break
                    else:
                        print(f"❓ 未知指令: {user_input}")
                    continue
                
                # 發送給 Agent 處理
                result = await self.send_message(user_input)
                
                # 格式化並顯示回應
                agent_response = self.format_agent_response(result)
                print(f"\n🤖 Agent: {agent_response}")
                
                # 永遠顯示詳細結果，以觀察 plan
                self.display_detailed_result(result)
                
                # 保存到歷史記錄
                self.conversation_history.append({
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'user_message': user_input,
                    'agent_response': agent_response
                })
                
            except KeyboardInterrupt:
                print("\n\n👋 收到中斷信號，正在退出...")
                break
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}")
                print("請重試或輸入 /quit 退出")

def main():
    """主函數"""
    tester = DatcomAgentTester()
    
    # 檢查 app 是否可用
    if not tester.app:
        print("❌ 無法初始化 DATCOM Agent App")
        print("請檢查以下項目:")
        print("1. agent/supervisor_v2.py 或 agent/supervisor.py 是否存在")
        print("2. 相關依賴是否正確安裝")
        print("3. 配置是否正確")
        return 1
    
    try:
        # 運行互動會話
        asyncio.run(tester.run_interactive_session())
        return 0
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
