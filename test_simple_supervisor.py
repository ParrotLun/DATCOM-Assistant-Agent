"""
簡化版的 Supervisor 測試 - 展示預建元件的使用
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

# 載入環境變數
load_dotenv()

def setup_llm():
    """設定語言模型"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 環境變數未設定")
    
    return ChatOpenAI(
        model=os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-oss-20b"),
        base_url=os.getenv("OPENAI_API_BASE_URL", "http://172.16.120.65:8089/v1"),
        temperature=0
    )

def create_simple_agents():
    """建立簡單的測試 Agents"""
    llm = setup_llm()
    
    # 簡化的 RAG Agent (使用 create_react_agent)
    rag_agent = create_react_agent(
        llm,
        tools=[],  # 暫時沒有工具
        prompt="你是資料查詢專家，專門回答使用者的問題。回覆必須使用繁體中文。",
        name="rag_agent"
    )
    
    # 簡化的 DATCOM Agent (使用 create_react_agent)
    datcom_agent = create_react_agent(
        llm,
        tools=[],  # 暫時沒有工具
        prompt="你是 DATCOM 檔案生成專家，專門建立航空動力學輸入檔案。回覆必須使用繁體中文。",
        name="datcom_agent"
    )
    
    return [rag_agent, datcom_agent]

def create_simple_supervisor():
    """建立簡化的 Supervisor"""
    llm = setup_llm()
    agents = create_simple_agents()
    
    supervisor_prompt = SystemMessage(content="""你是 DATCOM Assistant 的協調器。

可用的 Worker Agents：
- rag_agent: 處理資料查詢、分析、解釋等任務
- datcom_agent: 處理 DATCOM 檔案生成和驗證

決定使用哪個 agent 來完成使用者的請求。回覆必須使用繁體中文。""")
    
    return create_supervisor(
        agents=agents,
        model=llm,
        prompt=supervisor_prompt,
        supervisor_name="supervisor"
    )

def test_simple_supervisor():
    """測試簡化的 Supervisor"""
    try:
        print("🚀 建立簡化的 DATCOM Assistant...")
        supervisor = create_simple_supervisor()
        
        # 編譯並加入記憶體
        memory = InMemorySaver()
        app = supervisor.compile(checkpointer=memory)
        
        print("✅ 簡化版 Supervisor 建立成功！")
        print("\n🏗️ 架構特點：")
        print("- ✅ 使用 langgraph_supervisor.create_supervisor")
        print("- ✅ 使用 langgraph.prebuilt.create_react_agent")
        print("- ✅ 使用 InMemorySaver (短期記憶)")
        print("- ✅ 所有 agents 都有明確的名稱")
        
        # 簡單測試
        test_message = [HumanMessage(content="請解釋什麼是 DATCOM")]
        print(f"\n🧪 測試訊息: {test_message[0].content}")
        
        config = {"configurable": {"thread_id": "test-thread"}}
        response = app.invoke({"messages": test_message}, config=config)
        
        print("📤 回應:")
        if response and "messages" in response:
            for msg in response["messages"][-2:]:  # 顯示最後兩條訊息
                print(f"  {type(msg).__name__}: {msg.content[:100]}...")
        
        return app
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    app = test_simple_supervisor()
