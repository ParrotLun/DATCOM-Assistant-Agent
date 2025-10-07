from langchain_core.tools import tool

@tool
def submit_to_httpserver(content: str) -> dict:
    """將 DATCOM 內容提交到遠端伺服器進行驗證。

    Args:
        content: 要驗證的 DATCOM 檔案內容。

    Returns:
        一個包含驗證結果的字典。
        例如: {"status": "success"} 或 {"status": "failure", "error": "Invalid format"}
    """
    # 這是一個佔位符。實際的實作需要透過 HTTP 客戶端與遠端伺服器進行互動。
    print(f"--- 正在提交以下內容到伺服器 ---")
    print(content)
    print(f"---------------------------------")

    # 模擬成功的回應
    if "FAIL" in content.upper():
        return {"status": "failure", "error": "模擬的驗證失敗"}
    else:
        return {"status": "success"}
