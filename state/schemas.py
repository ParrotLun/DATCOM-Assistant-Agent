from typing import List, Literal, Optional, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph_supervisor import SupervisorState as BaseSupervisorState

# 全域共享的 Todo 項目結構  
class TodoItem(TypedDict):  
    task: str  
    status: Literal["pending", "completed"]

# 1. 全域 Supervisor State  
class SupervisorState(BaseSupervisorState):
    todo_list: List[TodoItem]  
    last_successful_datcom: Optional[Dict[str, Any]] # 改為字典格式儲存完整的 DATCOM 數據

# 2. DatcomAgent 的區域 State  
class DatcomAgentState(SupervisorState):  
    generated_content: Optional[Dict[str, Any]] # 改為字典格式
    validation_result: Optional[Dict[str, Any]] # 新增驗證結果
    submission_result: Optional[Dict[str, Any]] # 新增提交結果
    retry_count: int # 新增重試計數