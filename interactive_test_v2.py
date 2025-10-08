#!/usr/bin/env python3
"""
DATCOM Assistant Agent 互動測試腳本 V2

功能：
1. 即時顯示 Supervisor 的決策過程
2. 追蹤 Todo List 的變化
3. 顯示每個 Worker Agent 的執行狀態
4. 視覺化 State 的流動
5. 支援流式輸出（streaming）
"""

import sys
import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import json

# 添加項目路徑
sys.path.append(os.path.dirname(__file__))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

# 導入我們的組件
from agent.supervisor import app
from utils.todo_manager import format_todo_list, get_todo_summary


class ColorfulPrinter:
    """帶顏色的終端輸出"""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def header(text: str):
        print(f"\n{ColorfulPrinter.HEADER}{ColorfulPrinter.BOLD}{'='*70}{ColorfulPrinter.ENDC}")
        print(f"{ColorfulPrinter.HEADER}{ColorfulPrinter.BOLD}{text}{ColorfulPrinter.ENDC}")
        print(f"{ColorfulPrinter.HEADER}{ColorfulPrinter.BOLD}{'='*70}{ColorfulPrinter.ENDC}\n")

    @staticmethod
    def section(text: str):
        print(f"\n{ColorfulPrinter.OKBLUE}{ColorfulPrinter.BOLD}▶ {text}{ColorfulPrinter.ENDC}")
        print(f"{ColorfulPrinter.OKBLUE}{'─'*68}{ColorfulPrinter.ENDC}")

    @staticmethod
    def success(text: str):
        print(f"{ColorfulPrinter.OKGREEN}✓ {text}{ColorfulPrinter.ENDC}")

    @staticmethod
    def warning(text: str):
        print(f"{ColorfulPrinter.WARNING}⚠ {text}{ColorfulPrinter.ENDC}")

    @staticmethod
    def error(text: str):
        print(f"{ColorfulPrinter.FAIL}✗ {text}{ColorfulPrinter.ENDC}")

    @staticmethod
    def info(text: str):
        print(f"{ColorfulPrinter.OKCYAN}ℹ {text}{ColorfulPrinter.ENDC}")

    @staticmethod
    def agent(name: str, action: str):
        print(f"{ColorfulPrinter.BOLD}🤖 [{name}]{ColorfulPrinter.ENDC} {action}")


class DatcomAgentInteractiveTester:
    """增強版互動測試器"""

    def __init__(self):
        self.app = app
        self.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = {
            "configurable": {"thread_id": self.thread_id},
            "recursion_limit": 50
        }
        self.conversation_count = 0
        self.printer = ColorfulPrinter()

    def print_banner(self):
        """顯示歡迎橫幅"""
        self.printer.header("🚁 DATCOM Assistant Agent - 互動測試 V2")
        print("🎯 功能：")
        print("  • 即時追蹤 Supervisor 決策")
        print("  • 視覺化 Todo List 變化")
        print("  • 顯示 Worker Agent 執行狀態")
        print("  • State 流動追蹤\n")
        print("💬 範例對話：")
        print("  • '什麼是 DATCOM 的 FLTCON 區段？' - 觸發 RAG Agent")
        print("  • '請幫我生成一個戰鬥機的 DATCOM 檔案' - 觸發 DATCOM Agent")
        print("  • '先查詢 WGPLNF 參數說明，再生成檔案' - 觸發兩個 Agents\n")
        print("⌨️  指令：")
        print("  /help     - 顯示幫助")
        print("  /status   - 顯示系統狀態")
        print("  /state    - 顯示當前 State")
        print("  /clear    - 清空會話")
        print("  /quit     - 退出\n")

    def display_state_snapshot(self, state: Dict[str, Any], title: str = "當前 State"):
        """顯示 State 快照"""
        self.printer.section(f"📊 {title}")

        # Messages
        messages = state.get("messages", [])
        print(f"💬 Messages: {len(messages)} 條")
        if messages:
            for i, msg in enumerate(messages[-3:], 1):  # 只顯示最後 3 條
                msg_type = type(msg).__name__
                content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                print(f"   {i}. [{msg_type}] {content}")

        # Todo List
        todo_list = state.get("todo_list", [])
        if todo_list:
            print(f"\n📋 Todo List: {len(todo_list)} 項")
            summary = get_todo_summary(todo_list)
            print(f"   ⏳ Pending: {summary['pending']}")
            print(f"   ▶️  In Progress: {summary['in_progress']}")
            print(f"   ✅ Completed: {summary['completed']}")
            print(f"   ❌ Failed: {summary['failed']}")

            # 顯示詳細 Todos
            for i, todo in enumerate(todo_list, 1):
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "▶️",
                    "completed": "✅",
                    "failed": "❌"
                }.get(todo['status'], "❓")
                print(f"   {status_icon} {i}. {todo['task']}")
                if todo.get('error_message'):
                    self.printer.error(f"      Error: {todo['error_message']}")
        else:
            print(f"\n📋 Todo List: (空)")

        # Last Successful DATCOM
        datcom = state.get("last_successful_datcom")
        if datcom:
            case_id = datcom.get("case_id", "unknown")
            units = datcom.get("units", "unknown")
            print(f"\n✈️  Last DATCOM: {case_id} ({units})")
        else:
            print(f"\n✈️  Last DATCOM: (無)")

        # Remaining Steps
        remaining = state.get("remaining_steps", "N/A")
        print(f"\n🔢 Remaining Steps: {remaining}")
        print()

    def stream_agent_execution(self, user_input: str):
        """流式執行並顯示過程"""
        self.conversation_count += 1

        self.printer.header(f"對話 #{self.conversation_count}")
        self.printer.info(f"您的輸入: {user_input}")

        # 建立輸入
        input_state = {
            "messages": [HumanMessage(content=user_input)]
        }

        self.printer.section("🔄 執行流程追蹤")

        step_count = 0
        last_node = None

        try:
            # 使用 stream 模式執行
            for event in self.app.stream(input_state, self.config):
                step_count += 1

                # event 格式: {node_name: state_update}
                for node_name, state_update in event.items():
                    if node_name == "__start__":
                        self.printer.agent("SYSTEM", "啟動處理流程")
                        continue

                    if node_name == "__end__":
                        self.printer.agent("SYSTEM", "完成處理")
                        continue

                    # 顯示節點執行
                    print(f"\n┌─ Step {step_count}: {ColorfulPrinter.BOLD}{node_name}{ColorfulPrinter.ENDC}")

                    # 檢查是否是 Supervisor 決策
                    if node_name == "supervisor":
                        messages = state_update.get("messages", [])
                        if messages:
                            last_msg = messages[-1]
                            # 檢查是否有 tool_calls (代表 Supervisor 做出決策)
                            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                for tool_call in last_msg.tool_calls:
                                    agent_name = tool_call.get('name', 'unknown')
                                    self.printer.info(f"   Supervisor 決定調用: {agent_name}")

                    # 檢查是否是 Worker Agent
                    elif node_name in ["rag_agent", "datcom_agent"]:
                        self.printer.agent(node_name.upper(), "執行中...")

                        messages = state_update.get("messages", [])
                        if messages:
                            # 顯示 Agent 的輸出
                            for msg in messages[-2:]:  # 最後 2 條訊息
                                if isinstance(msg, AIMessage):
                                    content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                                    print(f"   📝 {content}")

                                    # 檢查是否有額外信息
                                    if hasattr(msg, 'additional_kwargs'):
                                        kwargs = msg.additional_kwargs
                                        if kwargs.get('success') is True:
                                            self.printer.success("   DATCOM 生成成功")
                                        elif kwargs.get('success') is False:
                                            self.printer.error("   DATCOM 生成失敗")

                    # 顯示 Todo List 變化
                    todo_list = state_update.get("todo_list")
                    if todo_list:
                        print(f"\n   📋 Todo List 更新:")
                        for todo in todo_list[-3:]:  # 最後 3 項
                            status_icon = {
                                "pending": "⏳",
                                "in_progress": "▶️",
                                "completed": "✅",
                                "failed": "❌"
                            }.get(todo['status'], "❓")
                            print(f"      {status_icon} {todo['task']}")

                    print(f"└{'─' * 50}")
                    last_node = node_name

            # 獲取最終 State
            final_state = self.app.get_state(self.config)

            # 顯示最終結果
            self.printer.section("📊 最終結果")

            messages = final_state.values.get("messages", [])
            if messages:
                last_message = messages[-1]
                print(f"\n🤖 Agent 回覆:\n")
                print(f"{last_message.content}\n")

            # 顯示完整 State
            self.display_state_snapshot(final_state.values, "最終 State 快照")

            return final_state.values

        except Exception as e:
            self.printer.error(f"執行錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None

    def show_status(self):
        """顯示系統狀態"""
        self.printer.section("📊 系統狀態")
        print(f"會話 ID: {self.thread_id}")
        print(f"對話次數: {self.conversation_count}")
        print(f"App 狀態: {'✅ 正常' if self.app else '❌ 錯誤'}")
        print(f"Checkpointer: {type(self.app.checkpointer).__name__ if hasattr(self.app, 'checkpointer') else 'N/A'}")

    def show_current_state(self):
        """顯示當前 State"""
        try:
            state = self.app.get_state(self.config)
            self.display_state_snapshot(state.values, "當前 State")
        except Exception as e:
            self.printer.error(f"無法獲取 State: {e}")

    def clear_session(self):
        """清空會話"""
        self.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = {
            "configurable": {"thread_id": self.thread_id},
            "recursion_limit": 50
        }
        self.conversation_count = 0
        self.printer.success("會話已清空，開始新會話")

    def show_help(self):
        """顯示幫助"""
        self.printer.section("📚 使用指南")

        print("🎯 測試 RAG Agent:")
        print("  • '什麼是 FLTCON？'")
        print("  • 'WGPLNF 參數有哪些？'")
        print("  • '解釋一下機翼後掠角的定義'\n")

        print("🎯 測試 DATCOM Agent:")
        print("  • '生成一個通用飛機的 DATCOM 檔案'")
        print("  • '建立戰鬥機 DATCOM 配置'")
        print("  • '幫我產生運輸機的輸入檔'\n")

        print("🎯 測試 Agent 協作:")
        print("  • '先查詢 SYNTHS 參數，再生成檔案'")
        print("  • '解釋 DATCOM 結構後建立範例'\n")

        print("⌨️  指令:")
        print("  /help     - 顯示此幫助")
        print("  /status   - 系統狀態")
        print("  /state    - 當前 State")
        print("  /clear    - 清空會話")
        print("  /quit     - 退出程式\n")

    def run(self):
        """運行互動會話"""
        self.print_banner()

        while True:
            try:
                # 獲取用戶輸入
                user_input = input(f"\n{ColorfulPrinter.BOLD}💭 您:{ColorfulPrinter.ENDC} ").strip()

                if not user_input:
                    continue

                # 處理指令
                if user_input.startswith('/'):
                    if user_input == '/help':
                        self.show_help()
                    elif user_input == '/status':
                        self.show_status()
                    elif user_input == '/state':
                        self.show_current_state()
                    elif user_input == '/clear':
                        self.clear_session()
                    elif user_input == '/quit':
                        self.printer.info("再見！感謝使用 DATCOM Assistant Agent")
                        break
                    else:
                        self.printer.warning(f"未知指令: {user_input}")
                    continue

                # 執行 Agent
                self.stream_agent_execution(user_input)

            except KeyboardInterrupt:
                print("\n")
                self.printer.warning("收到中斷信號")
                confirm = input("確定要退出嗎？(y/n): ").strip().lower()
                if confirm == 'y':
                    break
            except Exception as e:
                self.printer.error(f"發生錯誤: {e}")
                import traceback
                traceback.print_exc()


def main():
    """主函數"""
    tester = DatcomAgentInteractiveTester()

    if not tester.app:
        print("❌ 無法初始化 DATCOM Agent App")
        return 1

    try:
        tester.run()
        return 0
    except Exception as e:
        print(f"❌ 程式執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
