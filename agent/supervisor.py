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

# ============================================================
# 修補 ChatOpenAI 以支援本地模型（不支援 parallel_tool_calls）
# ============================================================

# 步驟 1: 修補 bind_tools - 強制設為 False
_original_bind_tools = ChatOpenAI.bind_tools

def _patched_bind_tools(self, tools, **kwargs):
    """修補的 bind_tools 方法，強制設定 parallel_tool_calls=False"""
    kwargs['parallel_tool_calls'] = False
    return _original_bind_tools(self, tools, **kwargs)

ChatOpenAI.bind_tools = _patched_bind_tools

# 步驟 2: 修補 _generate - 在發送請求前移除 parallel_tool_calls
_original_generate = ChatOpenAI._generate

def _patched_generate(self, messages, stop=None, run_manager=None, **kwargs):
    """修補的 _generate 方法，移除本地模型不支援的參數"""
    # 移除 parallel_tool_calls 參數（本地模型不接受）
    kwargs.pop('parallel_tool_calls', None)
    return _original_generate(self, messages, stop, run_manager, **kwargs)

ChatOpenAI._generate = _patched_generate
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
    """建立 DATCOM Worker Agent (使用完整的驗證-重試循環)

    返回已編譯的 datcom_agent_graph
    """
    from agent.datcom_agent import datcom_agent_graph

    print("   ✓ 使用完整的建立-驗證-重試循環")
    return datcom_agent_graph


def create_supervisor_system():
    """建立 Supervisor 系統

    架構：直接使用已編譯的 subgraphs 作為 agents
    create_supervisor 可以接受 compiled graphs
    """

    # 設定 LLM
    llm = setup_llm()

    # 建立 Worker Subgraphs (這些已經是 compiled graphs)
    print("🔧 建立 RAG Worker Subgraph...")
    rag_subgraph = create_rag_worker()

    print("🔧 建立 DATCOM Worker Subgraph...")
    datcom_subgraph = create_datcom_worker()

    # 直接傳給 create_supervisor
    # create_supervisor 會自動處理這些 compiled graphs
    agents = [rag_subgraph, datcom_subgraph]

    # Supervisor 系統提示
    supervisor_prompt = SystemMessage(content="""你是 DATCOM Assistant 的協調器。

職責：
1. 分析使用者請求
2. 決定需要哪些 Worker Agent 來完成任務
3. 協調 Worker Agents 之間的工作流程
4. 整理並回覆最終結果

可用的 Worker Agents：
- rag_agent: 處理資料查詢、分析、解釋 DATCOM 概念等任務
- datcom_agent: 處理 DATCOM 檔案生成和驗證（完整的驗證-重試循環）

工作原則：
- 如果任務涉及查詢資料或解釋概念，使用 rag_agent
- 如果任務涉及生成 DATCOM 檔案，使用 datcom_agent
- 可以讓兩個 agents 協作：先用 rag_agent 查詢需求，再用 datcom_agent 生成

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
