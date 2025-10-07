from typing import Dict, Any
from state.schemas import DatcomAgentState
from tool.datcom_tools import submit_to_httpserver

def build(state: DatcomAgentState) -> Dict[str, Any]:
    """根據 state 中的資料建立 DATCOM 內容。"""
    print("--- DatcomAgent: 正在建立內容 ---")
    # 佔位符：基於 messages 和 last_successful_datcom 建立內容
    rag_data = "從 RAG Agent 獲取的模擬資料"
    last_datcom = state.get("last_successful_datcom")
    
    content = f"# DATCOM 內容\n" \
              f"# RAG 資料: {rag_data}\n"
    if last_datcom:
        content += f"# 基於之前的成功版本: {last_datcom[:20]}...\n"
    
    # 為了測試重試機制，我們可以在這裡加入一個觸發失敗的邏輯
    # content += "FAIL"

    return {"generated_content": content}

def submit(state: DatcomAgentState) -> Dict[str, Any]:
    """將生成的內容提交到伺服器進行驗證。"""
    print("--- DatcomAgent: 正在提交內容以進行驗證 ---")
    content = state.get("generated_content")
    if not content:
        raise ValueError("generated_content 不能為空")
        
    result = submit_to_httpserver.invoke({"content": content})
    
    # 實際應用中，我們可能會將 result 存入 state 的某個臨時欄位
    # 這裡為了簡化，我們直接在下一個節點的 state 中處理
    print(f"--- DatcomAgent: 收到驗證結果: {result} ---")
    
    # 為了讓 check_retry 能拿到結果，我們將其放入 messages
    # 但更好的做法是放在 state 的一個臨時欄位中
    return {"messages": [str(result)]} # 簡單起見，轉為字串

def check_retry(state: DatcomAgentState) -> str:
    """檢查驗證結果，決定是結束還是重試。"""
    print("--- DatcomAgent: 正在檢查驗證結果 ---")
    last_message = state["messages"][-1]
    
    # 簡單地檢查訊息中是否包含 'failure'
    if "'status': 'failure'" in last_message:
        print("--- DatcomAgent: 驗證失敗，將要重試 ---")
        return "retry"
    else:
        print("--- DatcomAgent: 驗證成功，任務結束 ---")
        # 將成功的內容存起來
        return "finish"
