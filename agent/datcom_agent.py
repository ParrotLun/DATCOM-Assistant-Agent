from langgraph.graph import StateGraph
from state.schemas import DatcomAgentState
from node.datcom_nodes import build, submit, check_retry

# 建立 DatcomAgent 的 StateGraph
builder = StateGraph(DatcomAgentState)

# 定義節點
builder.add_node("build", build)
builder.add_node("submit", submit)

# 設定進入點
builder.set_entry_point("build")

# 定義邊
builder.add_edge("build", "submit")

# 定義條件邊，用於重試或結束
builder.add_conditional_edges(
    "submit",
    check_retry,
    {
        "retry": "build",  # 如果失敗，回到 build 重新開始
        "finish": "__end__" # 如果成功，結束這個子圖
    }
)

# 編譯 Graph
datcom_agent_graph = builder.compile()
