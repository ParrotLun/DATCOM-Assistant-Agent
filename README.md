# **DATCOM Assistant Agent \- 技術設計文件**

這份文件詳細記錄了 DATCOM 助理 agent 的架構、設計原則、元件職責和實作指南，旨在為開發提供清晰的藍圖。

## **1\. 核心理念與架構**

本專案遵循三大核心設計原則：**簡化、職責分離、數據結構優先**。

* **簡化 (Simplicity)**：優先使用 LangGraph 的預建元件 (`prebuilt components`)。只有在處理無法用預建元件解決的**有狀態循環 (stateful loops)或複雜條件分支**時，才建立客製化的 `StateGraph`。  
* **職責分離 (Separation of Concerns)**：系統中的每個元件都有單一且明確的職責。Supervisor 只負責協調，Worker Agent 只處理專業任務，工具 (Tools) 只執行一個具體動作。  
* **數據結構優先 (Data-Structure First)**：在撰寫任何程式碼之前，必須先清晰地定義狀態 (`State`) 的結構和數據在系統中的流動方式。

### **1.1. 專案架構：Supervisor/Worker 模式**

本專案採用由 `Supervisor` 協調的多 agent 系統架構，確保了系統的可擴展性和可維護性。

```
Code snippet  
flowchart TD  
    A(("使用者請求")) \--\> Supervisor{"Supervisor"}

    subgraph "Worker Agents"  
        RAG\_Agent\["RAG Agent\<br\>(處理 Agentic RAG)"\]  
        DatcomAgent\["Datcom Agent\<br\>(處理 DATCOM 檔案與驗證循環)"\]  
    end

    Supervisor \-- "需要資料" \--\> RAG\_Agent  
    RAG\_Agent \-- "資料好了" \--\> Supervisor  
    Supervisor \-- "資料給你，開始工作" \--\> DatcomAgent  
    DatcomAgent \-- "任務完成/失敗" \--\> Supervisor  
    Supervisor \--\> Z(("最終回覆"))
```


## **2\. 元件詳細敘述**

### **2.1. Supervisor (`agent/supervisor.py`)**

* **類型**：`langgraph-supervisor` 預建元件的客製化實作。  
* **職責**：  
  1. **總指揮**：作為整個 Graph 的入口和協調中心。  
  2. **規劃 (Planning)**：接收使用者請求後，第一個 `plan` 節點会分析請求，生成一份 `todo_list`，並將其存入全域狀態。此流程不需人為介入。  
  3. **任務分派**：根據 `todo_list` 的內容，將具體任務（如「查詢資料」或「建立 DATCOM」）分派給對應的 Worker Agent。  
  4. **最終回覆**：在所有任務完成後，整理 Worker Agent 的回報，生成最終的答覆給使用者。

### **2.2. RAG Agent (`agent/rag_agent/`)**

* **類型**：已存在的 LangGraph 子圖 (Subgraph)，被視為一個獨立的 Worker Agent。  
* **職責**：  
  * 專門處理所有與 Agentic RAG 相關的複雜查詢。  
  * 接收 Supervisor 傳遞的查詢任務，回傳經過整理和精煉的資料。  
  * 其產出（`rag_data`）會被封裝在 `ToolMessage` 中，透過 `messages` 列表傳遞，而不是直接寫入 State。

### **2.3. Datcom Agent (`agent/datcom_agent.py`)**

* **類型**：客製化的 `StateGraph`。  
* **職責**：  
  * 核心 Worker Agent，負責處理所有 DATCOM 檔案的生命週期。  
  * 其內部是一個小型的狀態機，專門處理一個**包含重試機制的驗證循環**。  
  * **內部流程**：  
    1. **建立內容 (Build)**：根據從 Supervisor 接收到的資料（包括 RAG 結果和歷史 DATCOM），在記憶體中建立 DATCOM 內容，並存入其區域 State 的 `generated_content` 欄位。  
    2. **提交驗證 (Submit)**：呼叫 `submit_to_httpserver` 工具，將 `generated_content` 傳送到遠端伺服器進行驗證。  
    3. **檢查與重試 (Check & Retry)**：分析伺服器的回覆。如果成功，則結束任務；如果失敗，則分析錯誤訊息，返回第一步修改內容，然後重新提交。

## **3\. 檔案結構**

專案必須嚴格遵守以下檔案結構，以確保程式碼的組織性和可讀性。

```
.  
├── agent/  
│   ├── supervisor.py         \# 主要的 Supervisor Graph，會匯出 app  
│   ├── datcom\_agent.py       \# DatcomAgent 的客製化 StateGraph  
│   └── rag\_agent/            \# Agentic RAG 子圖的資料夾  
│       └── ...               \# (已存在的 subgraph 檔案)  
│  
├── node/  
│   ├── datcom\_nodes.py       \# DatcomAgent 內部使用的所有節點函式  
│   └── supervisor\_nodes.py   \# Supervisor 的規劃 (plan) 節點函式  
│  
├── state/  
│   └── schemas.py            \# 定義所有 State 物件 (SupervisorState, DatcomAgentState)  
│  
├── tool/  
│   └── datcom\_tools.py       \# DatcomAgent 使用的工具 (例如: submit\_to\_httpserver)  
│  
├── langgraph.json            \# LangGraph 專案設定檔  
└── ...                     \# 其他專案檔案
```

## **4\. 狀態管理與數據流**

本專案的狀態管理遵循**分層設計**和**最小化原則**，以避免數據污染和狀態混亂。

### **4.1. State 分層設計**

* **全域 State (`SupervisorState`)**: 用於管理跨越多個任務、需要長期保存的狀態。這是整個系統的最高層級狀態。  
* **區域 State (`DatcomAgentState`)**: `DatcomAgent` 內部使用的 state，它**繼承**自 `SupervisorState`，並額外定義只在自身任務中需要的臨時欄位。

### **4.2. State 結構定義 (`state/schemas.py`)**

Python  
from typing import List, Literal, Optional, TypedDict  
from langchain\_core.messages import BaseMessage

\# 全域共享的 Todo 項目結構  
class TodoItem(TypedDict):  
    task: str  
    status: Literal\["pending", "completed"\]

\# 1\. 全域 Supervisor State  
class SupervisorState(TypedDict):  
    messages: List\[BaseMessage\]  
    todo\_list: List\[TodoItem\]  
    last\_successful\_datcom: Optional\[str\] \# 儲存上一次成功的產出，用於後續修改

\# 2\. DatcomAgent 的區域 State  
class DatcomAgentState(SupervisorState):  
    generated\_content: Optional\[str\] \# 任務內部的臨時數據

### **4.3. 數據傳遞原則**

1. **State 用於追蹤長期狀態和計畫**：只有像 `last_successful_datcom` 這樣需要在不同任務間共享或長期保存的數據，才應放在 `SupervisorState` 中。  
2. **Messages 用於傳遞短期數據**：Agent 之間的**一次性數據傳遞**（如 `RAG_Agent` 的 `rag_data`）**必須**使用 `messages` 列表（例如 `ToolMessage`）來完成。  
3. **區域 State 用於任務內部數據**：單一任務內部的臨時數據（如 `DatcomAgent` 的 `generated_content`）應儲存在其自己的區域 State 中。

## **5\. 關鍵技術要求**

* **啟用短期記憶 (Short-Term Memory)**：在 `supervisor.py` 中編譯主 Graph 時，**必須**加入 `MemorySaver` 作為 `checkpointer`，以追蹤對話狀態。 `graph = builder.compile(checkpointer=MemorySaver())`  
* **模型偏好 (Model Preference)**：開發時請使用模型 gpt-oss 20b(configuraiton在 .env file)
## **6\. GitHub Copilot 指南**

將以下文字作為專案的上下文，以引導 GitHub Copilot 進行開發。

"Copilot, we are building a LangGraph project with a Supervisor/Worker architecture. The main graph is in `agent/supervisor.py`, which delegates tasks to two workers: `RAG_Agent` and `DatcomAgent`. The `DatcomAgent` is a custom state machine defined in `agent/datcom_agent.py` that uses nodes from `node/datcom_nodes.py` and tools from `tool/datcom_tools.py` to handle a build-validate-retry loop. The project uses a layered state design defined in `state/schemas.py`: a global `SupervisorState` and a local `DatcomAgentState`. This project requires a `MemorySaver` checkpointer for short-term memory. Please follow the file structure and principles outlined in the project's technical design document."
