#!/usr/bin/env python3
"""
DATCOM Assistant Agent 互動測試腳本 V3

新增功能：
1. 詳細的 RAG 檢索追蹤 - 顯示檢索到的文檔
2. Tool 呼叫監控 - 追蹤每個 tool 的使用
3. Supervisor Todo List 顯示
4. 更深入的執行流程視覺化
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
    GRAY = '\033[90m'

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
    def subsection(text: str):
        print(f"\n{ColorfulPrinter.OKCYAN}  ► {text}{ColorfulPrinter.ENDC}")

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
    def debug(text: str):
        print(f"{ColorfulPrinter.GRAY}🔍 {text}{ColorfulPrinter.ENDC}")

    @staticmethod
    def agent(name: str, action: str):
        print(f"{ColorfulPrinter.BOLD}🤖 [{name}]{ColorfulPrinter.ENDC} {action}")


class EnhancedDatcomTester:
    """增強版測試器 - 追蹤 RAG 檢索和 Todo"""

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
        self.printer.header("🚁 DATCOM Assistant Agent - 互動測試 V3 (增強版)")
        print("🎯 新功能：")
        print("  • 📚 RAG 檢索細節追蹤 - 看到實際檢索的文檔")
        print("  • 🔧 Tool 呼叫監控 - 追蹤工具使用")
        print("  • 📋 Supervisor Todo List - 即時任務狀態")
        print("  • 🔍 深度執行流程追蹤\n")
        print("💬 測試範例：")
        print("  • '什麼是 FLTCON？' - 看 RAG 如何檢索文檔")
        print("  • 'WGPLNF 參數有哪些？' - 觀察檢索過程")
        print("  • '生成 DATCOM 檔案' - 看 DATCOM Agent 流程\n")
        print("⌨️  指令：")
        print("  /help     - 顯示幫助")
        print("  /status   - 顯示系統狀態")
        print("  /state    - 顯示當前 State")
        print("  /clear    - 清空會話")
        print("  /quit     - 退出\n")

    def extract_tool_calls(self, message) -> List[Dict[str, Any]]:
        """從訊息中提取 tool calls"""
        tool_calls = []
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for call in message.tool_calls:
                tool_calls.append({
                    'name': call.get('name', 'unknown'),
                    'args': call.get('args', {}),
                    'id': call.get('id', 'unknown')
                })
        return tool_calls

    def extract_rag_results(self, message) -> Dict[str, Any]:
        """從 ToolMessage 中提取 RAG 檢索結果"""
        if not isinstance(message, ToolMessage):
            return None

        # 檢查是否是檢索工具的結果
        tool_name = getattr(message, 'name', '')
        if 'retrieve' not in tool_name.lower():
            return None

        try:
            # 嘗試解析內容
            content = message.content
            if isinstance(content, str):
                # 可能是 JSON 字串
                try:
                    data = json.loads(content)
                    return data
                except:
                    # 或者是純文字
                    return {'text': content[:500]}
            return content
        except:
            return None

    def display_tool_calls(self, tool_calls: List[Dict[str, Any]]):
        """顯示 Tool 呼叫詳情"""
        if not tool_calls:
            return

        self.printer.subsection("🔧 Tool 呼叫")
        for i, call in enumerate(tool_calls, 1):
            tool_name = call['name']
            args = call['args']

            print(f"   {i}. {ColorfulPrinter.BOLD}{tool_name}{ColorfulPrinter.ENDC}")

            # 特別處理 RAG 相關的 tools
            if 'retrieve' in tool_name.lower():
                self.printer.debug(f"      📚 檢索查詢: {args.get('query', args.get('question', 'N/A'))}")
                if 'top_k' in args:
                    self.printer.debug(f"      📊 返回數量: {args['top_k']}")

            elif 'router' in tool_name.lower():
                self.printer.debug(f"      🧭 路由查詢: {args.get('question', 'N/A')}")

            elif 'datcom' in tool_name.lower():
                self.printer.debug(f"      ✈️  DATCOM 操作: {list(args.keys())}")

            else:
                # 其他 tools - 顯示主要參數
                if args:
                    key_params = list(args.keys())[:3]  # 只顯示前 3 個參數
                    self.printer.debug(f"      參數: {', '.join(key_params)}")

    def display_rag_results(self, rag_data: Any, tool_name: str = ""):
        """顯示 RAG 檢索結果"""
        self.printer.subsection(f"📚 RAG 檢索結果 ({tool_name})")

        if isinstance(rag_data, dict):
            # 檢查常見的檢索結果格式
            if 'documents' in rag_data:
                docs = rag_data['documents']
                print(f"   找到 {len(docs)} 篇文檔:")
                for i, doc in enumerate(docs[:3], 1):  # 只顯示前 3 篇
                    title = doc.get('title', doc.get('source', f'Doc {i}'))
                    content = doc.get('content', doc.get('text', ''))
                    print(f"   {i}. {ColorfulPrinter.BOLD}{title}{ColorfulPrinter.ENDC}")
                    print(f"      {content[:100]}...")

            elif 'results' in rag_data:
                results = rag_data['results']
                print(f"   檢索到 {len(results)} 筆結果")

            elif 'text' in rag_data:
                text = rag_data['text']
                print(f"   內容: {text[:200]}...")

            else:
                # 未知格式 - 顯示 keys
                print(f"   數據結構: {list(rag_data.keys())}")

        elif isinstance(rag_data, str):
            print(f"   結果: {rag_data[:300]}...")

        elif isinstance(rag_data, list):
            print(f"   找到 {len(rag_data)} 個項目")
            for i, item in enumerate(rag_data[:2], 1):
                print(f"   {i}. {str(item)[:100]}...")

    def display_todo_list(self, todo_list: List[Dict]):
        """顯示 Todo List"""
        if not todo_list:
            return

        self.printer.subsection("📋 Supervisor Todo List")
        summary = get_todo_summary(todo_list)

        print(f"   總計: {summary['total']} | "
              f"⏳ {summary['pending']} | "
              f"▶️ {summary['in_progress']} | "
              f"✅ {summary['completed']} | "
              f"❌ {summary['failed']}")

        for i, todo in enumerate(todo_list, 1):
            status_icon = {
                "pending": "⏳",
                "in_progress": "▶️",
                "completed": "✅",
                "failed": "❌"
            }.get(todo['status'], "❓")

            print(f"   {status_icon} {i}. {todo['task']}")
            if todo.get('error_message'):
                self.printer.error(f"      {todo['error_message']}")

    def stream_agent_execution(self, user_input: str):
        """流式執行並顯示詳細過程"""
        self.conversation_count += 1

        self.printer.header(f"對話 #{self.conversation_count}")
        self.printer.info(f"您的輸入: {user_input}")

        # 建立輸入
        input_state = {
            "messages": [HumanMessage(content=user_input)]
        }

        self.printer.section("🔄 執行流程追蹤")

        step_count = 0
        last_todo_list = []

        try:
            # 使用 stream 模式執行
            for event in self.app.stream(input_state, self.config):
                step_count += 1

                # event 格式: {node_name: state_update}
                for node_name, state_update in event.items():
                    if node_name in ["__start__", "__end__"]:
                        continue

                    # 顯示節點執行
                    print(f"\n┌─ Step {step_count}: {ColorfulPrinter.BOLD}{node_name}{ColorfulPrinter.ENDC}")

                    # 顯示 Todo List 變化
                    current_todo = state_update.get("todo_list", [])
                    if current_todo and current_todo != last_todo_list:
                        self.display_todo_list(current_todo)
                        last_todo_list = current_todo

                    # 處理訊息
                    messages = state_update.get("messages", [])
                    if messages:
                        for msg in messages[-3:]:  # 最後 3 條訊息
                            # 檢查 AI Message 的 tool calls
                            if isinstance(msg, AIMessage):
                                tool_calls = self.extract_tool_calls(msg)
                                if tool_calls:
                                    self.display_tool_calls(tool_calls)

                                # 顯示 AI 回覆內容
                                if msg.content:
                                    content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                                    print(f"\n   💬 AI: {content}")

                            # 檢查 Tool Message 的 RAG 結果
                            elif isinstance(msg, ToolMessage):
                                tool_name = getattr(msg, 'name', 'unknown_tool')
                                rag_data = self.extract_rag_results(msg)

                                if rag_data:
                                    self.display_rag_results(rag_data, tool_name)
                                else:
                                    # 顯示一般 tool 結果
                                    result = msg.content
                                    if isinstance(result, str) and len(result) > 0:
                                        print(f"\n   🔧 Tool 結果 ({tool_name}): {result[:100]}...")

                    print(f"└{'─' * 66}")

            # 獲取最終 State
            final_state = self.app.get_state(self.config)

            # 顯示最終結果
            self.printer.section("📊 最終結果")

            messages = final_state.values.get("messages", [])
            if messages:
                last_message = messages[-1]
                print(f"\n🤖 Agent 回覆:\n")
                print(f"{last_message.content}\n")

            # 顯示最終 Todo List
            final_todos = final_state.values.get("todo_list", [])
            if final_todos:
                self.printer.subsection("📋 最終 Todo 狀態")
                self.display_todo_list(final_todos)

            # 顯示 State 摘要
            self.display_state_summary(final_state.values)

            return final_state.values

        except Exception as e:
            self.printer.error(f"執行錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None

    def display_state_summary(self, state: Dict[str, Any]):
        """顯示 State 摘要"""
        self.printer.subsection("📊 State 摘要")

        # Messages 數量
        msg_count = len(state.get("messages", []))
        print(f"   💬 Messages: {msg_count} 條")

        # Last DATCOM
        datcom = state.get("last_successful_datcom")
        if datcom:
            case_id = datcom.get("case_id", "unknown")
            print(f"   ✈️  Last DATCOM: {case_id}")

        # Remaining Steps
        remaining = state.get("remaining_steps", "N/A")
        print(f"   🔢 Remaining Steps: {remaining}")

    def show_help(self):
        """顯示幫助"""
        self.printer.section("📚 使用指南")

        print("🎯 測試 RAG 檢索:")
        print("  • '什麼是 FLTCON？'")
        print("  • 'WGPLNF 參數說明'")
        print("  • '機翼後掠角如何定義？'\n")

        print("🎯 測試 DATCOM Agent:")
        print("  • '生成通用飛機 DATCOM 檔案'")
        print("  • '建立戰鬥機配置'\n")

        print("🔍 V3 新功能:")
        print("  • 自動顯示 RAG 檢索到的文檔")
        print("  • 追蹤每個 tool 的呼叫")
        print("  • 即時顯示 Supervisor Todo List")
        print("  • 深入的執行流程視覺化\n")

    def show_status(self):
        """顯示系統狀態"""
        self.printer.section("📊 系統狀態")
        print(f"會話 ID: {self.thread_id}")
        print(f"對話次數: {self.conversation_count}")
        print(f"App 狀態: {'✅ 正常' if self.app else '❌ 錯誤'}")

    def show_current_state(self):
        """顯示當前 State"""
        try:
            state = self.app.get_state(self.config)
            self.display_state_summary(state.values)

            # 顯示當前 Todo List
            todos = state.values.get("todo_list", [])
            if todos:
                print()
                self.display_todo_list(todos)
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
                        self.printer.info("再見！")
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
    tester = EnhancedDatcomTester()

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
