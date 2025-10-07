from typing import Dict, Any
from state.schemas import SupervisorState

def plan(state: SupervisorState) -> Dict[str, Any]:
    """根據使用者請求生成一個計畫 (todo_list)。"""
    print("--- Supervisor: 正在規劃任務 ---")
    # 這是一個佔位符。實際的實作需要一個 LLM 來分析 messages 並生成 todo_list。
    # 模擬一個固定的計畫。
    todo_list = [
        {"task": "查詢 RAG 資料", "status": "pending"},
        {"task": "建立 DATCOM 檔案", "status": "pending"},
    ]
    return {"todo_list": todo_list}
