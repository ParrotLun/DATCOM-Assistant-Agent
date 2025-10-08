from typing import Dict, Any
from langchain_core.messages import AIMessage, ToolMessage
from state.schemas import DatcomAgentState
from tool.datcom_tools import (
    validate_datcom_format,
    send_datcom_to_subgraph,
    check_datcom_completeness,
    create_datcom_template
)
import json

def build(state: DatcomAgentState) -> Dict[str, Any]:
    """根據 state 中的資料建立 DATCOM 內容。

    遵循設計原則：
    1. 從 messages 中提取用戶需求
    2. 根據 validation_errors 調整生成策略（如果是重試）
    3. 生成結果存入 generated_content
    4. 驗證錯誤存入 validation_errors
    """
    print("--- DatcomAgent: 正在建立內容 ---")

    # 從狀態中獲取信息
    messages = state.get("messages", [])
    retry_count = state.get("retry_count", 0)
    validation_errors = state.get("validation_errors", [])

    # 提取用戶需求（從最近的人類訊息）
    user_requirements = _extract_user_requirements(messages)

    # 如果是重試，調整生成策略
    if retry_count > 0:
        print(f"--- DatcomAgent: 第 {retry_count} 次重試 ---")
        print(f"--- 前次錯誤: {validation_errors} ---")

    # 根據重試次數調整飛機類型（模擬不同策略）
    aircraft_types = ["generic", "fighter", "transport"]
    aircraft_type = aircraft_types[retry_count % len(aircraft_types)]

    # 生成 DATCOM 內容
    try:
        generated_content = create_datcom_template.invoke({
            "case_id": f"user_case_{retry_count + 1}",
            "aircraft_type": aircraft_type
        })

        print(f"--- DatcomAgent: 生成了 {aircraft_type} 類型的 DATCOM 內容 ---")

        # 立即進行本地驗證
        validation_result = validate_datcom_format.invoke({
            "datcom_content": json.dumps(generated_content)
        })

        is_valid = validation_result.is_valid
        errors = validation_result.errors if hasattr(validation_result, 'errors') else []

        print(f"--- DatcomAgent: 本地驗證結果: {'通過' if is_valid else '失敗'} ---")

        # 將驗證結果加入 messages（遵循「Messages 傳遞短期數據」原則）
        new_message = AIMessage(
            content=f"已生成 {aircraft_type} 類型 DATCOM 內容。驗證: {'✓ 通過' if is_valid else '✗ 失敗'}",
            additional_kwargs={
                "validation_result": {
                    "is_valid": is_valid,
                    "errors": errors
                }
            }
        )

        return {
            "generated_content": generated_content,
            "validation_errors": errors,
            "messages": [new_message]
        }

    except Exception as e:
        error_msg = f"生成 DATCOM 內容時發生錯誤: {str(e)}"
        print(f"--- DatcomAgent: {error_msg} ---")

        return {
            "validation_errors": [error_msg],
            "messages": [AIMessage(content=f"❌ {error_msg}")]
        }

def _extract_user_requirements(messages: list) -> str:
    """從訊息歷史中提取用戶需求"""
    if not messages:
        return "生成通用 DATCOM 檔案"

    # 找到最後一條人類訊息
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == "human":
            return msg.content
        elif hasattr(msg, 'content'):
            return msg.content

    return "生成通用 DATCOM 檔案"

def validate(state: DatcomAgentState) -> Dict[str, Any]:
    """驗證生成的 DATCOM 內容（完整性檢查）

    遵循設計原則：
    1. 檢查 generated_content 是否存在
    2. 驗證數據完整性
    3. 錯誤訊息存入 validation_errors
    4. 驗證結果透過 messages 傳遞
    """
    print("--- DatcomAgent: 正在驗證 DATCOM 完整性 ---")

    content = state.get("generated_content")
    validation_errors = state.get("validation_errors", [])

    # 檢查是否有內容
    if not content:
        error_msg = "沒有可驗證的 DATCOM 內容"
        print(f"--- DatcomAgent: 錯誤 - {error_msg} ---")
        return {
            "validation_errors": [error_msg],
            "messages": [AIMessage(content=f"❌ {error_msg}")]
        }

    # 如果本地驗證已經失敗，跳過完整性檢查
    if validation_errors:
        print("--- DatcomAgent: 本地格式驗證失敗，跳過完整性檢查 ---")
        return {}  # 保持當前 validation_errors

    # 檢查數據完整性
    try:
        completeness_result = check_datcom_completeness.invoke({
            "datcom_data": content
        })

        score = completeness_result['completeness_score']
        is_complete = completeness_result['is_complete']
        missing = completeness_result.get('missing_required', [])

        print(f"--- DatcomAgent: 完整性評分: {score} ---")

        if not is_complete:
            error_msg = f"數據不完整 (評分: {score})"
            errors = [f"{error_msg}: 缺少 {', '.join(missing)}"]
            print(f"--- DatcomAgent: {errors[0]} ---")

            return {
                "validation_errors": errors,
                "messages": [AIMessage(
                    content=f"⚠️ DATCOM 數據不完整\n缺少組件: {', '.join(missing)}",
                    additional_kwargs={"completeness_result": completeness_result}
                )]
            }
        else:
            print("--- DatcomAgent: 完整性檢查通過 ---")
            return {
                "messages": [AIMessage(
                    content=f"✓ DATCOM 數據完整性驗證通過 (評分: {score})",
                    additional_kwargs={"completeness_result": completeness_result}
                )]
            }

    except Exception as e:
        error_msg = f"完整性檢查時發生錯誤: {str(e)}"
        print(f"--- DatcomAgent: {error_msg} ---")
        return {
            "validation_errors": [error_msg],
            "messages": [AIMessage(content=f"❌ {error_msg}")]
        }

def check_retry(state: DatcomAgentState) -> str:
    """檢查驗證結果，決定是結束還是重試。

    決策邏輯：
    1. 如果沒有 validation_errors -> 成功 -> finish
    2. 如果 retry_count >= max_retries -> 失敗放棄 -> finish
    3. 否則 -> 重試 -> retry
    """
    print("--- DatcomAgent: 檢查驗證結果 ---")

    validation_errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # 檢查是否成功
    if not validation_errors:
        print("--- DatcomAgent: ✓ 驗證成功，任務完成 ---")
        return "success"

    # 檢查是否達到最大重試次數
    if retry_count >= max_retries:
        print(f"--- DatcomAgent: ✗ 已達到最大重試次數 ({max_retries})，停止重試 ---")
        return "failed"

    # 還有重試機會
    print(f"--- DatcomAgent: ⟳ 準備第 {retry_count + 1} 次重試 ---")
    print(f"--- 錯誤: {validation_errors[0] if validation_errors else 'Unknown'} ---")
    return "retry"

def update_retry_count(state: DatcomAgentState) -> Dict[str, Any]:
    """更新重試計數

    在每次重試前調用，增加 retry_count
    """
    current_count = state.get("retry_count", 0)
    new_count = current_count + 1
    print(f"--- DatcomAgent: 更新重試計數: {current_count} -> {new_count} ---")
    return {"retry_count": new_count}

def finalize_success(state: DatcomAgentState) -> Dict[str, Any]:
    """成功完成時的最終處理

    將成功的 DATCOM 數據包裝為訊息返回
    這個結果會被 Supervisor 的 wrapper 轉換為 SupervisorState
    """
    print("--- DatcomAgent: 成功完成，準備最終輸出 ---")

    content = state.get("generated_content")
    case_id = content.get("case_id", "unknown") if content else "unknown"

    success_message = AIMessage(
        content=f"✅ DATCOM 檔案生成成功\n案例 ID: {case_id}\n已通過所有驗證",
        additional_kwargs={
            "success": True,
            "datcom_content": content
        }
    )

    return {"messages": [success_message]}

def finalize_failure(state: DatcomAgentState) -> Dict[str, Any]:
    """失敗時的最終處理

    將失敗訊息和錯誤詳情包裝為訊息返回
    """
    print("--- DatcomAgent: 失敗，準備錯誤報告 ---")

    validation_errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)

    error_summary = "\n".join(f"  - {err}" for err in validation_errors[:3])  # 最多顯示3個錯誤

    failure_message = AIMessage(
        content=f"❌ DATCOM 檔案生成失敗\n已重試 {retry_count} 次\n\n錯誤摘要:\n{error_summary}",
        additional_kwargs={
            "success": False,
            "errors": validation_errors,
            "retry_count": retry_count
        }
    )

    return {"messages": [failure_message]}
