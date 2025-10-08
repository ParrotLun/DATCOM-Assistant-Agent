"""
State 轉換適配器 (State Adapters)

用途：
在 Supervisor 和各個 Worker Agent 之間轉換 State
- SupervisorState <-> DatcomAgentState
- SupervisorState <-> GraphState (RAG)

遵循設計原則：
1. 全域 State 和區域 State 分離
2. 只傳遞必要的數據
3. 使用 messages 傳遞短期數據
"""
from typing import Dict, Any, Callable
from langchain_core.messages import BaseMessage, AIMessage
from state.schemas import SupervisorState, DatcomAgentState, TodoItem


# ============================================================
# DATCOM Agent Wrapper
# ============================================================
def create_datcom_agent_wrapper(datcom_subgraph) -> Callable:
    """建立 DATCOM Agent 的 Wrapper

    功能：
    1. 將 SupervisorState 轉換為 DatcomAgentState
    2. 調用 datcom_subgraph
    3. 將結果轉回 SupervisorState
    4. 更新 todo_list 和 last_successful_datcom

    Args:
        datcom_subgraph: 編譯後的 DATCOM Agent graph

    Returns:
        wrapper function 可作為 Supervisor 的 node
    """

    def wrapper_node(state: SupervisorState) -> Dict[str, Any]:
        """DATCOM Agent Wrapper Node"""
        print("🔄 [State Adapter] 轉換 SupervisorState -> DatcomAgentState")

        # 1. 提取需要的數據
        messages = state.get("messages", [])

        # 2. 建立 DatcomAgentState 輸入
        datcom_input = {
            "messages": messages,
            "generated_content": None,
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": 3
        }

        print(f"🔄 [State Adapter] 調用 DATCOM Agent Subgraph")

        # 3. 執行 DATCOM Agent
        try:
            result = datcom_subgraph.invoke(datcom_input)
        except Exception as e:
            print(f"❌ [State Adapter] DATCOM Agent 執行錯誤: {e}")
            return {
                "messages": [AIMessage(content=f"DATCOM Agent 執行失敗: {str(e)}")]
            }

        print(f"🔄 [State Adapter] 轉換 DatcomAgentState -> SupervisorState")

        # 4. 從結果中提取數據
        result_messages = result.get("messages", [])
        generated_content = result.get("generated_content")

        # 5. 檢查是否成功（從最後一條訊息的 additional_kwargs）
        last_message = result_messages[-1] if result_messages else None
        is_success = False
        datcom_content = None

        if last_message and hasattr(last_message, 'additional_kwargs'):
            kwargs = last_message.additional_kwargs
            is_success = kwargs.get("success", False)
            datcom_content = kwargs.get("datcom_content")

        # 6. 組裝返回的 SupervisorState
        output = {"messages": result_messages}

        # 7. 如果成功，更新 last_successful_datcom
        if is_success and datcom_content:
            output["last_successful_datcom"] = datcom_content
            print(f"✅ [State Adapter] DATCOM 生成成功，已更新 last_successful_datcom")
        else:
            print(f"⚠️ [State Adapter] DATCOM 生成未成功")

        return output

    return wrapper_node


# ============================================================
# RAG Agent Wrapper
# ============================================================
def create_rag_agent_wrapper(rag_subgraph) -> Callable:
    """建立 RAG Agent 的 Wrapper

    功能：
    1. 將 SupervisorState 轉換為 GraphState
    2. 調用 rag_subgraph
    3. 將結果轉回 SupervisorState

    Args:
        rag_subgraph: 編譯後的 RAG Agent graph

    Returns:
        wrapper function 可作為 Supervisor 的 node
    """

    def wrapper_node(state: SupervisorState) -> Dict[str, Any]:
        """RAG Agent Wrapper Node"""
        print("🔄 [State Adapter] 轉換 SupervisorState -> GraphState (RAG)")

        # 1. 提取 messages
        messages = state.get("messages", [])

        # 2. 建立 GraphState 輸入
        # RAG Agent 支援兩種模式：standalone (question) 和 subgraph (messages)
        rag_input = {
            "messages": messages,
            "question": "",
            "generation": "",
            "collection": "",
            "retrieved_docs": []
        }

        print(f"🔄 [State Adapter] 調用 RAG Agent Subgraph")

        # 3. 執行 RAG Agent
        try:
            result = rag_subgraph.invoke(rag_input)
        except Exception as e:
            print(f"❌ [State Adapter] RAG Agent 執行錯誤: {e}")
            return {
                "messages": [AIMessage(content=f"RAG Agent 執行失敗: {str(e)}")]
            }

        print(f"🔄 [State Adapter] 轉換 GraphState -> SupervisorState")

        # 4. 提取結果
        result_messages = result.get("messages", [])

        # 5. 返回 SupervisorState 格式
        return {"messages": result_messages}

    return wrapper_node


# ============================================================
# 測試和調試用
# ============================================================
def debug_state_transition(from_state: Dict[str, Any], to_state: Dict[str, Any], agent_name: str):
    """調試 State 轉換過程"""
    print(f"\n{'='*60}")
    print(f"🔍 State 轉換調試: {agent_name}")
    print(f"{'='*60}")
    print(f"輸入 State keys: {list(from_state.keys())}")
    print(f"輸出 State keys: {list(to_state.keys())}")

    # 檢查 messages 數量變化
    input_msg_count = len(from_state.get("messages", []))
    output_msg_count = len(to_state.get("messages", []))
    print(f"Messages: {input_msg_count} -> {output_msg_count} (+{output_msg_count - input_msg_count})")

    # 檢查其他欄位變化
    for key in to_state.keys():
        if key != "messages":
            old_val = from_state.get(key, "N/A")
            new_val = to_state.get(key, "N/A")
            if old_val != new_val:
                print(f"{key}: {old_val} -> {new_val}")

    print(f"{'='*60}\n")
