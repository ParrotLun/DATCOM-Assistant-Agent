from typing import List, Literal, Optional, TypedDict  
from langchain_core.messages import BaseMessage

# 全域共享的 Todo 項目結構  
class TodoItem(TypedDict):  
    task: str  
    status: Literal["pending", "completed"]

# 1. 全域 Supervisor State  
class SupervisorState(TypedDict):  
    messages: List[BaseMessage]  
    todo_list: List[TodoItem]  
    last_successful_datcom: Optional[str] # 儲存上一次成功的產出，用於後續修改

# 2. DatcomAgent 的區域 State  
class DatcomAgentState(SupervisorState):  
    generated_content: Optional[str] # 任務內部的臨時數據