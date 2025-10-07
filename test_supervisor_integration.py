#!/usr/bin/env python3
"""
測試 Supervisor 與 RAG Agent 整合
"""
import uuid
from typing import cast
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

# 載入環境變數
load_dotenv()

# 匯入我們的 supervisor app
from agent.supervisor import app
from state.schemas import SupervisorState

def test_rag_query():
    """測試 RAG 查詢功能"""
    print("=== 測試 RAG 查詢功能 ===")
    
    # 建立一個會觸發 RAG Agent 的初始狀態
    config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state: SupervisorState = {
        "messages": [HumanMessage(content="請解釋 DATCOM 有什麼功能？")],
        "todo_list": [
            {
                "task": "查詢 DATCOM 功能：分析並解釋 DATCOM 軟體的主要功能",
                "status": "pending"
            }
        ],
        "last_successful_datcom": None
    }
    
    print("初始狀態：")
    print(f"  問題: {initial_state['messages'][0].content}")
    print(f"  Todo: {initial_state['todo_list'][0]['task']}")
    print()
    
    try:
        print("開始執行 Supervisor 工作流程...")
        result = app.invoke(initial_state, config=config)
        
        print("\n=== 執行結果 ===")
        print(f"Todo 列表: {len(result.get('todo_list', []))} 個項目")
        print(f"訊息數量: {len(result.get('messages', []))} 條")
        
        # 檢查最後的訊息（應該是 RAG Agent 的回答）
        messages = result.get('messages', [])
        if messages:
            last_message = messages[-1]
            print(f"\n最終回答:")
            print(f"  類型: {type(last_message).__name__}")
            print(f"  內容: {last_message.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_datcom_query():
    """測試 DATCOM Agent 功能"""
    print("\n=== 測試 DATCOM Agent 功能 ===")
    
    config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state: SupervisorState = {
        "messages": [HumanMessage(content="請建立一個 DATCOM 檔案")],
        "todo_list": [
            {
                "task": "建立 DATCOM 檔案：生成一個完整的 DATCOM 輸入檔案",
                "status": "pending"
            }
        ],
        "last_successful_datcom": None
    }
    
    print("初始狀態：")
    print(f"  問題: {initial_state['messages'][0].content}")
    print(f"  Todo: {initial_state['todo_list'][0]['task']}")
    print()
    
    try:
        print("開始執行 Supervisor 工作流程...")
        result = app.invoke(initial_state, config=config)
        
        print("\n=== 執行結果 ===")
        print(f"Todo 列表: {len(result.get('todo_list', []))} 個項目")
        print(f"訊息數量: {len(result.get('messages', []))} 條")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試 Supervisor 與 Agent 整合")
    
    # 測試 RAG 查詢
    rag_success = test_rag_query()
    
    # 測試 DATCOM Agent  
    datcom_success = test_datcom_query()
    
    print("\n" + "="*50)
    print(f"RAG Agent 測試: {'✅ 成功' if rag_success else '❌ 失敗'}")
    print(f"DATCOM Agent 測試: {'✅ 成功' if datcom_success else '❌ 失敗'}")
    
    if rag_success and datcom_success:
        print("\n🎉 所有測試通過！Supervisor 整合成功！")
    else:
        print("\n⚠️  部分測試失敗，需要進一步調試")
