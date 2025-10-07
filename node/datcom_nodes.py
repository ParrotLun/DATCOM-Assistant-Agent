from typing import Dict, Any
from state.schemas import DatcomAgentState
from tool.datcom_tools import (
    validate_datcom_format,
    send_datcom_to_subgraph,
    check_datcom_completeness,
    create_datcom_template
)
import json

def build(state: DatcomAgentState) -> Dict[str, Any]:
    """根據 state 中的資料建立 DATCOM 內容。"""
    print("--- DatcomAgent: 正在建立內容 ---")
    
    # 從狀態中獲取信息來決定生成內容
    messages = state.get("messages", [])
    last_datcom = state.get("last_successful_datcom")
    retry_count = state.get("retry_count", 0)
    
    # 如果是重試，可以基於之前的錯誤調整生成策略
    if retry_count > 0:
        print(f"--- DatcomAgent: 第 {retry_count} 次重試，調整生成策略 ---")
    
    # 這裡應該有 LLM 生成邏輯，目前使用模板作為示例
    # 在實際應用中，這裡會調用 LLM 來根據用戶需求生成 DATCOM 數據
    
    # 根據重試次數調整飛機類型，模擬不同的生成策略
    aircraft_types = ["generic", "fighter", "transport"]
    aircraft_type = aircraft_types[retry_count % len(aircraft_types)]
    
    # 生成 DATCOM 內容
    generated_content = create_datcom_template.invoke({
        "case_id": f"generated_case_{retry_count + 1}",
        "aircraft_type": aircraft_type
    })
    
    print(f"--- DatcomAgent: 生成了 {aircraft_type} 類型的 DATCOM 內容 ---")
    
    # 立即進行本地驗證
    validation_result = validate_datcom_format.invoke({
        "datcom_content": json.dumps(generated_content)
    })
    
    print(f"--- DatcomAgent: 本地驗證結果: {'通過' if validation_result.is_valid else '失敗'} ---")
    
    return {
        "generated_content": generated_content,
        "validation_result": validation_result.model_dump() if hasattr(validation_result, 'model_dump') else validation_result.__dict__
    }

def submit(state: DatcomAgentState) -> Dict[str, Any]:
    """將生成的內容提交到子圖節點進行驗證。"""
    print("--- DatcomAgent: 正在提交內容到子圖節點 ---")
    
    content = state.get("generated_content")
    validation_result = state.get("validation_result", {})
    
    if not content:
        print("--- DatcomAgent: 錯誤 - 沒有生成的內容可以提交 ---")
        return {
            "submission_result": {
                "status": "failure",
                "error": "沒有內容可提交"
            }
        }
    
    # 檢查本地驗證結果
    if not validation_result.get("is_valid", False):
        print("--- DatcomAgent: 本地驗證失敗，無法提交 ---")
        return {
            "submission_result": {
                "status": "failure",
                "error": "本地驗證失敗",
                "validation_errors": validation_result.get("errors", [])
            }
        }
    
    # 檢查數據完整性
    completeness_result = check_datcom_completeness.invoke({
        "datcom_data": content
    })
    
    print(f"--- DatcomAgent: 完整性評分: {completeness_result['completeness_score']} ---")
    
    if not completeness_result["is_complete"]:
        print(f"--- DatcomAgent: 數據不完整: {completeness_result['missing_required']} ---")
        return {
            "submission_result": {
                "status": "failure",
                "error": "數據不完整",
                "missing_components": completeness_result["missing_required"],
                "recommendations": completeness_result["recommendations"]
            }
        }
    
    # 發送到子圖節點
    print("--- DatcomAgent: 正在發送到子圖節點進行深度驗證 ---")
    
    subgraph_result = send_datcom_to_subgraph.invoke({
        "validated_datcom": content,
        "target_node": "datcom_verification_subgraph"
    })
    
    print(f"--- DatcomAgent: 子圖提交結果: {subgraph_result['status']} ---")
    print(f"--- DatcomAgent: {subgraph_result['message']} ---")
    
    # 如果成功，保存為最後一次成功的 DATCOM
    if subgraph_result.get("status") == "success":
        return {
            "submission_result": subgraph_result,
            "last_successful_datcom": content
        }
    else:
        return {"submission_result": subgraph_result}

def check_retry(state: DatcomAgentState) -> str:
    """檢查驗證結果，決定是結束還是重試。"""
    print("--- DatcomAgent: 正在檢查提交結果 ---")
    
    submission_result = state.get("submission_result", {})
    retry_count = state.get("retry_count", 0)
    max_retries = 3  # 最大重試次數
    
    # 檢查提交狀態
    status = submission_result.get("status", "unknown")
    
    if status == "success":
        print("--- DatcomAgent: 驗證成功，任務完成 ---")
        return "finish"
    
    # 檢查是否達到最大重試次數
    if retry_count >= max_retries:
        print(f"--- DatcomAgent: 已達到最大重試次數 ({max_retries})，停止重試 ---")
        return "finish"
    
    # 如果失敗且還有重試機會
    error_msg = submission_result.get("error", "未知錯誤")
    print(f"--- DatcomAgent: 驗證失敗 ({error_msg})，準備第 {retry_count + 1} 次重試 ---")
    
    return "retry"

def update_retry_count(state: DatcomAgentState) -> Dict[str, Any]:
    """更新重試計數的輔助函數"""
    current_count = state.get("retry_count", 0)
    return {"retry_count": current_count + 1}
