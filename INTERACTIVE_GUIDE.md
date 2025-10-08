# 互動測試腳本使用指南

## 📖 概述

`interactive_test_v2.py` 是一個增強版的互動測試工具，讓你可以：

1. **即時追蹤** Supervisor 的決策過程
2. **視覺化** Todo List 的變化（如果有實作）
3. **監控** 每個 Worker Agent 的執行狀態
4. **觀察** State 在各個節點間的流動

---

## 🚀 快速開始

### 方式 1: 自動示範

```bash
python3 demo_interactive.py
```

這會執行兩個測試案例：
- 測試 RAG Agent (查詢問題)
- 測試 DATCOM Agent (生成檔案)

你可以看到完整的執行流程和 State 變化。

### 方式 2: 直接互動

```bash
python3 interactive_test_v2.py
```

進入互動模式，可以自由輸入問題。

---

## 💬 測試範例

### 測試 RAG Agent

這些問題會觸發 RAG Agent 去查詢知識庫：

```
什麼是 FLTCON？
WGPLNF 參數有哪些？
解釋一下機翼後掠角的定義
DATCOM 的輸入檔案結構是什麼？
```

**你會看到：**
```
┌─ Step 1: supervisor
│  ℹ Supervisor 決定調用: rag_agent
└──────────────────────────────────────────────────

┌─ Step 2: rag_agent
│  🤖 [RAG_AGENT] 執行中...
│  📝 FLTCON 是 DATCOM 的飛行條件輸入區段...
└──────────────────────────────────────────────────
```

### 測試 DATCOM Agent

這些請求會觸發 DATCOM Agent 生成檔案：

```
生成一個通用飛機的 DATCOM 檔案
建立戰鬥機 DATCOM 配置
幫我產生運輸機的輸入檔
請建立一個 DATCOM 測試案例
```

**你會看到：**
```
┌─ Step 1: supervisor
│  ℹ Supervisor 決定調用: datcom_agent
└──────────────────────────────────────────────────

┌─ Step 2: datcom_agent
│  🤖 [DATCOM_AGENT] 執行中...
│  📝 已生成 generic 類型 DATCOM 內容。驗證: ✓ 通過
│  ✓ DATCOM 生成成功
└──────────────────────────────────────────────────

┌─ Step 3: supervisor
│  (整理結果並回覆用戶)
└──────────────────────────────────────────────────
```

### 測試 Agent 協作

這些請求可能需要多個 Agent 協作：

```
先查詢 SYNTHS 參數說明，再生成一個範例檔案
解釋 DATCOM 的結構，然後建立一個測試案例
查詢機翼參數定義，並用這些參數生成配置
```

**你會看到：**
```
┌─ Step 1: supervisor
│  ℹ Supervisor 決定調用: rag_agent
└──────────────────────────────────────────────────

┌─ Step 2: rag_agent
│  📝 SYNTHS 參數用於定義飛機配置...
└──────────────────────────────────────────────────

┌─ Step 3: supervisor
│  ℹ Supervisor 決定調用: datcom_agent
└──────────────────────────────────────────────────

┌─ Step 4: datcom_agent
│  📝 已生成 DATCOM 檔案...
└──────────────────────────────────────────────────
```

---

## 🎯 輸出說明

### 1. 執行流程追蹤

每個 Step 會顯示：

```
┌─ Step N: node_name
│  <node 的執行信息>
│  <決策信息>
│  <輸出內容>
└──────────────────────────────────────────────────
```

### 2. Supervisor 決策

當 Supervisor 決定調用某個 Worker 時：

```
ℹ Supervisor 決定調用: rag_agent
```

### 3. Agent 執行狀態

當 Worker Agent 執行時：

```
🤖 [DATCOM_AGENT] 執行中...
📝 <Agent 的輸出摘要>
✓ DATCOM 生成成功
```

或

```
✗ DATCOM 生成失敗
```

### 4. Todo List 更新（如果有實作）

當 Todo List 變化時：

```
📋 Todo List 更新:
   ⏳ 查詢 DATCOM 文檔
   ▶️ 生成 DATCOM 檔案
   ✅ 驗證檔案格式
```

### 5. 最終 State 快照

每次對話結束後會顯示：

```
▶ 📊 最終 State 快照
────────────────────────────────────────────────────────────────────

💬 Messages: 6 條
   1. [HumanMessage] 請生成一個通用飛機的 DATCOM 檔案
   2. [AIMessage] 我會幫您生成 DATCOM 檔案...
   3. [AIMessage] ✅ DATCOM 檔案生成成功...

📋 Todo List: 3 項
   ⏳ Pending: 0
   ▶️  In Progress: 0
   ✅ Completed: 3
   ❌ Failed: 0

   ✅ 1. 分析用戶需求
   ✅ 2. 生成 DATCOM 內容
   ✅ 3. 驗證檔案格式

✈️  Last DATCOM: user_case_1 (FT)

🔢 Remaining Steps: 7
```

---

## ⌨️ 指令說明

在互動模式中，你可以使用這些指令：

### `/help`
顯示完整的使用幫助和測試範例

### `/status`
顯示系統狀態：
```
📊 系統狀態
────────────────────────────────────────────────────────────────────
會話 ID: session_20251008_143022
對話次數: 3
App 狀態: ✅ 正常
Checkpointer: InMemorySaver
```

### `/state`
顯示當前的完整 State（包含所有欄位）

### `/clear`
清空當前會話，開始新的對話
- 會生成新的 thread_id
- 重置對話計數
- 清空 State

### `/quit`
退出程式

---

## 🔍 調試技巧

### 1. 觀察 Supervisor 如何決策

輸入不同類型的問題，看 Supervisor 如何選擇 Worker：

```
# 明確的查詢問題 -> rag_agent
什麼是 FLTCON？

# 明確的生成請求 -> datcom_agent
生成 DATCOM 檔案

# 模糊的請求 -> 看 Supervisor 的判斷
幫我處理 DATCOM
```

### 2. 追蹤 State 變化

使用 `/state` 指令在不同階段查看 State：

```
你: 生成檔案
(執行完成)
你: /state
(查看 State - 應該有 last_successful_datcom)

你: 再生成一個
(執行完成)
你: /state
(查看 State - last_successful_datcom 是否更新)
```

### 3. 測試錯誤處理

嘗試觸發錯誤情況：

```
# 空輸入
你:
(應該被忽略)

# 無意義輸入
你: asdfasdf
(看 Supervisor 如何處理)

# 超出範圍的請求
你: 幫我訂披薩
(看 Agent 如何回應)
```

### 4. 測試 DATCOM Agent 的重試機制

理論上，如果 DATCOM 生成失敗，Agent 會重試（最多 3 次）：

```
你: 生成 DATCOM 檔案
(觀察內部流程，看是否有重試)
```

**注意**：目前的實作中，模板生成通常會成功，所以可能看不到重試。
如果要測試重試，需要修改 `create_datcom_template` 讓它有機會失敗。

---

## 🎨 顏色說明

輸出使用顏色來區分不同類型的信息：

- **紫色粗體** - 標題和區塊分隔
- **藍色** - 信息性輸出
- **綠色** - 成功訊息
- **黃色** - 警告訊息
- **紅色** - 錯誤訊息
- **青色** - 一般信息

---

## 📊 範例對話流程

完整的對話流程範例：

```
💭 您: 請生成一個戰鬥機的 DATCOM 檔案

======================================================================
對話 #1
======================================================================

ℹ 您的輸入: 請生成一個戰鬥機的 DATCOM 檔案

▶ 🔄 執行流程追蹤
────────────────────────────────────────────────────────────────────

┌─ Step 1: supervisor
   ℹ Supervisor 決定調用: datcom_agent
└──────────────────────────────────────────────────────────────────

┌─ Step 2: datcom_agent
   🤖 [DATCOM_AGENT] 執行中...
   📝 已生成 fighter 類型 DATCOM 內容。驗證: ✓ 通過
   ✓ DATCOM 生成成功
└──────────────────────────────────────────────────────────────────

┌─ Step 3: supervisor
   (整理結果)
└──────────────────────────────────────────────────────────────────

▶ 📊 最終結果
────────────────────────────────────────────────────────────────────

🤖 Agent 回覆:

✅ DATCOM 檔案生成成功
案例 ID: user_case_1
已通過所有驗證

▶ 📊 最終 State 快照
────────────────────────────────────────────────────────────────────

💬 Messages: 4 條
   1. [HumanMessage] 請生成一個戰鬥機的 DATCOM 檔案
   2. [AIMessage] 我會為您生成戰鬥機的 DATCOM 檔案...
   3. [AIMessage] ✅ DATCOM 檔案生成成功...
   4. [AIMessage] 已完成 DATCOM 檔案生成...

✈️  Last DATCOM: user_case_1 (FT)

🔢 Remaining Steps: 7
```

---

## 🐛 疑難排解

### 問題：沒有看到顏色輸出

**原因**：某些終端機不支援 ANSI 顏色代碼

**解決**：
- 使用支援顏色的終端（如 VSCode Terminal、iTerm2、GNOME Terminal）
- 或者修改 `ColorfulPrinter` 類別移除顏色代碼

### 問題：看不到 Supervisor 的決策

**原因**：可能 Supervisor 沒有輸出 tool_calls

**檢查**：
- 確認 `create_supervisor` 正確設定
- 查看 `event` 的內容是否包含決策信息

### 問題：Todo List 一直是空的

**原因**：目前的實作中，Supervisor 還沒有整合 Todo Manager

**下一步**：需要在 Supervisor 或 Worker nodes 中加入 Todo CRUD 操作

---

## 📝 後續改進建議

1. **Todo List 整合**
   - 在 Supervisor node 中使用 `todo_manager` 建立和更新 todos
   - 在 Worker 開始前標記 `in_progress`
   - 完成後標記 `completed` 或 `failed`

2. **更詳細的進度追蹤**
   - 顯示每個 node 的執行時間
   - 顯示 LLM token 使用量
   - 顯示 checkpointer 的狀態

3. **互動功能增強**
   - 支援編輯上一次輸入
   - 支援對話歷史查詢
   - 支援匯出對話記錄

4. **視覺化**
   - 生成流程圖
   - State 變化的動畫
   - Todo List 的進度條

---

## 🎓 學習目標

使用這個互動測試工具，你應該能夠：

1. ✅ 理解 Supervisor 如何分析用戶輸入並選擇 Worker
2. ✅ 觀察 State 如何在不同 nodes 間流動
3. ✅ 看到 DATCOM Agent 的完整驗證-重試循環
4. ✅ 理解 Messages 如何用於傳遞短期數據
5. ✅ 掌握如何調試和追蹤 LangGraph 應用

---

開始探索吧！🚀

```bash
python3 interactive_test_v2.py
```
