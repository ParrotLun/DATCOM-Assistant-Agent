from typing import List, Literal, Optional, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState

# ============================================================
# Todo 項目結構
# ============================================================
class TodoItem(TypedDict):
    task: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    error_message: Optional[str]  # 新增錯誤訊息欄位

# ============================================================
# 1. 全域 Supervisor State
# 遵循原則：全域 State 只包含需要跨 Worker 共享的長期狀態
# ============================================================
class SupervisorState(MessagesState):
    """Supervisor 全域狀態

    - messages: 繼承自 MessagesState，儲存對話歷史
    - todo_list: 追蹤任務執行進度
    - last_successful_datcom: 儲存最後一次成功生成的 DATCOM 資料
    - remaining_steps: create_supervisor 需要的步數限制欄位
    """
    todo_list: List[TodoItem] = []  # 預設空列表
    last_successful_datcom: Optional[Dict[str, Any]] = None
    remaining_steps: int = 10  # Supervisor 最大執行步數

# ============================================================
# 2. DatcomAgent 的區域 State
# 遵循原則：區域 State 只繼承 MessagesState，不繼承全域 State
# ============================================================
class DatcomAgentState(MessagesState):
    """DATCOM Agent 區域狀態

    用於 DATCOM Agent 內部的建立-驗證-重試循環
    - messages: 繼承自 MessagesState
    - generated_content: 當前生成的 DATCOM 內容
    - validation_errors: 驗證錯誤列表
    - retry_count: 當前重試次數
    """
    generated_content: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = []  # 驗證錯誤列表
    retry_count: int = 0
    max_retries: int = 3  # 最大重試次數

# ============================================================
# 3. RAG Agent State (已在 rag_system/state.py 定義)
# 這裡只做參考註解
# ============================================================
# class GraphState(MessagesState):
#     question: str = ""
#     generation: str = ""
#     collection: str = ""
#     retrieved_docs: list = []