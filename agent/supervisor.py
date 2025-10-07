"""
使用 langgraph_supervisor 的重構版本
遵循設計原則：優先使用預建元件
"""
import os
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

# 載入環境變數
load_dotenv()

from state.schemas import SupervisorState
from tool.datcom_tools import validate_datcom_format, create_datcom_template, check_datcom_completeness

# RAG Agent 整合
from services.rag_agent.rag_system.subgraph import create_rag_subgraph
from services.rag_agent.rag_system.config import RAGConfig
from agent.datcom_agent import datcom_agent_graph


def setup_llm():
    """設定語言模型"""
    # 從環境變數讀取配置
    api_base = os.getenv("OPENAI_API_BASE_URL", "http://172.16.120.65:8089/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-oss-20b")
    
    # 確保 API key 存在
    if not api_key:
        raise ValueError("OPENAI_API_KEY 環境變數未設定")
    
    return ChatOpenAI(
        model=model,
        base_url=api_base,
        temperature=0
    )


def create_rag_worker():
    """建立 RAG Worker Agent (已經使用 create_react_agent)"""
    rag_config = RAGConfig.from_env()
    
    client = httpx.Client(
        verify=rag_config.verify_ssl,
        follow_redirects=True,
        timeout=httpx.Timeout(120.0, connect=10.0)
    )
    
    os.environ["OPENAI_API_KEY"] = rag_config.embed_api_key or ""
    
    llm = ChatOpenAI(
        model=rag_config.chat_model,
        base_url=rag_config.llm_api_base or rag_config.embed_api_base,
        temperature=rag_config.temperature,
        http_client=client
    )
    
    # create_rag_subgraph 已經回傳一個已編譯的圖形
    rag_subgraph = create_rag_subgraph(llm, rag_config, name="rag_agent")
    return rag_subgraph


def create_datcom_worker():
    """建立 DATCOM Worker Agent (使用 create_react_agent)"""
    llm = setup_llm()
    
    # DATCOM 工具列表
    tools = [validate_datcom_format, create_datcom_template, check_datcom_completeness]
    
    # 使用 create_react_agent 建立 DATCOM Agent
    system_prompt = """你是 DATCOM 檔案生成與驗證專家。

職責：
1. 使用 `create_datcom_template` 為使用者建立一個 DATCOM 檔案的起點。
2. 使用 `validate_datcom_format` 驗證使用者提供的 DATCOM 資料是否符合 Pydantic 模型。
3. 使用 `check_datcom_completeness` 檢查資料的完整性。
4. 根據驗證和檢查的結果，引導使用者修正或補全資料。

你的目標是協助使用者產生一個完整且格式正確的 DATCOM 輸入資料結構。

回覆必須使用繁體中文。"""
    
    return create_react_agent(
        llm,
        tools,
        prompt=system_prompt,
        name="datcom_agent"
    )


def create_supervisor_system():
    """建立使用預建元件的 Supervisor 系統"""
    
    # 設定 LLM
    llm = setup_llm()
    
    # 建立 Worker Agents
    print("🔧 建立 RAG Worker Agent...")
    rag_agent = create_rag_worker()
    
    print("🔧 建立 DATCOM Worker Agent...")
    datcom_agent = create_datcom_worker()
    
    # Worker Agents 列表
    agents = [rag_agent, datcom_agent]
    
    # Supervisor 系統提示
    supervisor_prompt = SystemMessage(content="""你是 DATCOM Assistant 的協調器。

職責：
1. 分析使用者請求
2. 決定需要哪些 Worker Agent 來完成任務
3. 協調 Worker Agents 之間的工作流程
4. 整理並回覆最終結果

可用的 Worker Agents：
- rag_agent: 處理資料查詢、分析、解釋等任務
- datcom_agent: 處理 DATCOM 檔案生成和驗證

工作原則：
- 如果任務涉及查詢資料或解釋概念，先使用 rag_agent
- 如果任務涉及生成檔案，使用 datcom_agent
- 必要時可以讓兩個 agents 協作完成複雜任務

回覆必須使用繁體中文。""")
    
    # 使用 create_supervisor 建立 Supervisor
    print("🔧 建立 Supervisor...")
    supervisor_graph = create_supervisor(
        agents=agents,
        model=llm,
        prompt=supervisor_prompt,
        state_schema=SupervisorState,
        supervisor_name="supervisor"
    )
    
    # 編譯並加入記憶體
    print("🔧 編譯圖形並加入記憶體...")
    memory = InMemorySaver()
    
    return supervisor_graph.compile(checkpointer=memory)


# 建立應用程式
print("🚀 正在建立 DATCOM Assistant Agent...")
app = create_supervisor_system()
print("✅ 應用程式建立完成！")

# 展示架構
def show_architecture():
    """展示新的架構設計"""
    print("\n" + "="*50)
    print("🏗️ DATCOM Assistant Agent - 重構後架構")
    print("="*50)
    print("✅ Supervisor: 使用 create_supervisor")
    print("✅ RAG Agent: 使用 create_react_agent (在 rag_system/node.py)")
    print("✅ DATCOM Agent: 使用 create_react_agent (新重構)")
    print()
    print("📋 預建元件使用情況:")
    print("- ✅ langgraph_supervisor.create_supervisor")
    print("- ✅ langgraph.prebuilt.create_react_agent")
    print("- ✅ InMemorySaver (短期記憶)")
    print()
    print("🎯 Entry Points:")
    print("- 主要: agent/supervisor_v2.py:app")
    print("- 配置: langgraph.json")
    print("- 測試: test_supervisor_integration.py")

if __name__ == "__main__":
    show_architecture()
