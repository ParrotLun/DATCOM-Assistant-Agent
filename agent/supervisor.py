from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from state.schemas import SupervisorState
from node.supervisor_nodes import plan
from agent.datcom_agent import datcom_agent_graph

# 主 Supervisor Graph
builder = StateGraph(SupervisorState)

# 加入節點
builder.add_node("plan", plan)

# --- RAG Agent --- #
# 這裡我們會加入 RAG Agent 作為一個節點。
# 由於 rag_agent 是已存在的子圖，我們先用一個註解佔位。
# builder.add_node("rag_agent", rag_agent_graph)

# --- Datcom Agent --- #
builder.add_node("datcom_agent", datcom_agent_graph)

# 設定進入點
builder.set_entry_point("plan")

# --- 定義邊 --- #
# 根據計畫，決定下一個步驟。
# 為了簡化，我們先建立一個線性流程：plan -> datcom_agent
# 實際應用中，這裡會有一個條件邊來決定要去哪個 worker。
builder.add_edge("plan", "datcom_agent")

# 當 datcom_agent 完成後，結束流程
builder.add_edge("datcom_agent", "__end__")

# --- 編譯 Graph --- #
# 根據 README 要求，加入 MemorySaver 作為 checkpointer
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

# 根據 README 要求，匯出為 app
app = graph

# --- 以下為一個簡單的執行範例，用於測試 ---
# if __name__ == "__main__":
#     import uuid
#     config = {"configurable": {"thread_id": str(uuid.uuid4())}}
#     initial_state = {"messages": [("human", "請建立一個 DATCOM 檔案")]}
#     
#     print("--- 開始執行 Supervisor ---")
#     for event in app.stream(initial_state, config=config):
#         for key, value in event.items():
#             print(f"事件: {key}")
#             print(value)
#             print("\n---\n")
#     print("--- Supervisor 執行完畢 ---")
