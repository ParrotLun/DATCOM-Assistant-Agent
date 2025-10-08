"""
DATCOM Agent - 完整的建立-驗證-重試循環

架構：
1. build: 根據用戶需求生成 DATCOM 內容
2. validate: 驗證生成的內容（格式 + 完整性）
3. check_retry: 決定成功/失敗/重試
4. update_retry_count: 重試前更新計數
5. finalize_success: 成功時的最終處理
6. finalize_failure: 失敗時的最終處理

流程：
  build -> validate -> check_retry
                          ├─> success -> finalize_success -> END
                          ├─> failed -> finalize_failure -> END
                          └─> retry -> update_retry_count -> build
"""
from langgraph.graph import StateGraph, END
from state.schemas import DatcomAgentState
from node.datcom_nodes import (
    build,
    validate,
    check_retry,
    update_retry_count,
    finalize_success,
    finalize_failure
)

# ============================================================
# 建立 DATCOM Agent StateGraph
# ============================================================
builder = StateGraph(DatcomAgentState)

# 定義所有節點
builder.add_node("build", build)
builder.add_node("validate", validate)
builder.add_node("update_retry_count", update_retry_count)
builder.add_node("finalize_success", finalize_success)
builder.add_node("finalize_failure", finalize_failure)

# 設定進入點
builder.set_entry_point("build")

# 定義流程邊
builder.add_edge("build", "validate")
builder.add_edge("update_retry_count", "build")  # 重試回到 build
builder.add_edge("finalize_success", END)
builder.add_edge("finalize_failure", END)

# 定義條件邊：根據驗證結果決定下一步
builder.add_conditional_edges(
    "validate",
    check_retry,
    {
        "success": "finalize_success",      # 成功 -> 最終處理 -> 結束
        "failed": "finalize_failure",       # 失敗 -> 錯誤報告 -> 結束
        "retry": "update_retry_count"       # 重試 -> 更新計數 -> 重新 build
    }
)

# 編譯 Graph (加上名稱以便 Supervisor 識別)
datcom_agent_graph = builder.compile(name="datcom_agent")

# ============================================================
# 輔助函數：顯示架構圖
# ============================================================
def show_graph_structure():
    """顯示 DATCOM Agent 的完整流程結構"""
    print("\n" + "="*60)
    print("🛠️  DATCOM Agent 架構")
    print("="*60)
    print("流程：")
    print("  START")
    print("    ↓")
    print("  [build] 生成 DATCOM 內容")
    print("    ↓")
    print("  [validate] 驗證格式與完整性")
    print("    ↓")
    print("  {check_retry} 決策點")
    print("    ├─→ success → [finalize_success] → END")
    print("    ├─→ failed  → [finalize_failure] → END")
    print("    └─→ retry   → [update_retry_count] ──┐")
    print("                                          ↓")
    print("                         ←────────────────┘")
    print("                       (回到 build)")
    print("="*60)
    print()

if __name__ == "__main__":
    show_graph_structure()
