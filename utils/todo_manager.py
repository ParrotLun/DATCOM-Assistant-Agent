"""
Todo List CRUD 操作管理器

提供完整的 Todo List 操作功能：
- Create: 建立新 Todo
- Read: 查詢 Todo 狀態
- Update: 更新 Todo 狀態
- Delete: 刪除 Todo

用於 Supervisor 追蹤任務執行進度
"""
from typing import List, Optional, Dict, Any
from state.schemas import TodoItem


# ============================================================
# Create - 建立 Todo
# ============================================================
def create_todo(
    todo_list: List[TodoItem],
    task: str,
    status: str = "pending"
) -> List[TodoItem]:
    """建立新的 Todo 項目

    Args:
        todo_list: 現有的 todo list
        task: 任務描述
        status: 初始狀態 (預設 "pending")

    Returns:
        更新後的 todo list
    """
    new_todo: TodoItem = {
        "task": task,
        "status": status,
        "error_message": None
    }

    return todo_list + [new_todo]


def create_multiple_todos(
    todo_list: List[TodoItem],
    tasks: List[str]
) -> List[TodoItem]:
    """批量建立多個 Todo

    Args:
        todo_list: 現有的 todo list
        tasks: 任務描述列表

    Returns:
        更新後的 todo list
    """
    new_list = todo_list.copy()
    for task in tasks:
        new_list = create_todo(new_list, task)
    return new_list


# ============================================================
# Read - 查詢 Todo
# ============================================================
def get_todo_by_task(todo_list: List[TodoItem], task: str) -> Optional[TodoItem]:
    """根據任務描述查找 Todo

    Args:
        todo_list: todo list
        task: 任務描述

    Returns:
        找到的 Todo 或 None
    """
    for todo in todo_list:
        if todo["task"] == task:
            return todo
    return None


def get_todos_by_status(todo_list: List[TodoItem], status: str) -> List[TodoItem]:
    """根據狀態篩選 Todos

    Args:
        todo_list: todo list
        status: 狀態 ("pending", "in_progress", "completed", "failed")

    Returns:
        符合條件的 Todos
    """
    return [todo for todo in todo_list if todo["status"] == status]


def get_todo_summary(todo_list: List[TodoItem]) -> Dict[str, int]:
    """獲取 Todo 統計摘要

    Returns:
        {
            "total": 總數,
            "pending": 待處理,
            "in_progress": 進行中,
            "completed": 已完成,
            "failed": 失敗
        }
    """
    summary = {
        "total": len(todo_list),
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "failed": 0
    }

    for todo in todo_list:
        status = todo["status"]
        if status in summary:
            summary[status] += 1

    return summary


# ============================================================
# Update - 更新 Todo
# ============================================================
def update_todo_status(
    todo_list: List[TodoItem],
    task: str,
    new_status: str,
    error_message: Optional[str] = None
) -> List[TodoItem]:
    """更新 Todo 的狀態

    Args:
        todo_list: todo list
        task: 要更新的任務描述
        new_status: 新狀態
        error_message: 錯誤訊息（可選，用於 failed 狀態）

    Returns:
        更新後的 todo list
    """
    updated_list = []

    for todo in todo_list:
        if todo["task"] == task:
            # 更新這個 todo
            updated_todo: TodoItem = {
                "task": todo["task"],
                "status": new_status,
                "error_message": error_message
            }
            updated_list.append(updated_todo)
        else:
            # 保持原樣
            updated_list.append(todo)

    return updated_list


def mark_todo_completed(todo_list: List[TodoItem], task: str) -> List[TodoItem]:
    """將 Todo 標記為完成

    Args:
        todo_list: todo list
        task: 任務描述

    Returns:
        更新後的 todo list
    """
    return update_todo_status(todo_list, task, "completed")


def mark_todo_failed(
    todo_list: List[TodoItem],
    task: str,
    error_message: str
) -> List[TodoItem]:
    """將 Todo 標記為失敗

    Args:
        todo_list: todo list
        task: 任務描述
        error_message: 錯誤訊息

    Returns:
        更新後的 todo list
    """
    return update_todo_status(todo_list, task, "failed", error_message)


def mark_todo_in_progress(todo_list: List[TodoItem], task: str) -> List[TodoItem]:
    """將 Todo 標記為進行中

    Args:
        todo_list: todo list
        task: 任務描述

    Returns:
        更新後的 todo list
    """
    return update_todo_status(todo_list, task, "in_progress")


# ============================================================
# Delete - 刪除 Todo
# ============================================================
def delete_todo(todo_list: List[TodoItem], task: str) -> List[TodoItem]:
    """刪除指定的 Todo

    Args:
        todo_list: todo list
        task: 要刪除的任務描述

    Returns:
        更新後的 todo list
    """
    return [todo for todo in todo_list if todo["task"] != task]


def clear_completed_todos(todo_list: List[TodoItem]) -> List[TodoItem]:
    """清除所有已完成的 Todos

    Args:
        todo_list: todo list

    Returns:
        只包含未完成 Todos 的 list
    """
    return [todo for todo in todo_list if todo["status"] != "completed"]


def clear_all_todos(todo_list: List[TodoItem]) -> List[TodoItem]:
    """清空所有 Todos

    Returns:
        空 list
    """
    return []


# ============================================================
# 輔助函數
# ============================================================
def format_todo_list(todo_list: List[TodoItem]) -> str:
    """將 Todo List 格式化為易讀的字串

    Args:
        todo_list: todo list

    Returns:
        格式化的字串
    """
    if not todo_list:
        return "📋 Todo List: (空)"

    lines = ["📋 Todo List:"]
    for i, todo in enumerate(todo_list, 1):
        status = todo["status"]
        task = todo["task"]

        # 狀態圖標
        status_icon = {
            "pending": "⏳",
            "in_progress": "▶️",
            "completed": "✅",
            "failed": "❌"
        }.get(status, "❓")

        line = f"  {i}. {status_icon} {task}"

        # 如果有錯誤訊息，加上
        if todo.get("error_message"):
            line += f"\n     ⚠️ {todo['error_message']}"

        lines.append(line)

    return "\n".join(lines)


def print_todo_list(todo_list: List[TodoItem]):
    """列印 Todo List（調試用）"""
    print(format_todo_list(todo_list))


# ============================================================
# 使用範例
# ============================================================
if __name__ == "__main__":
    # 示範 CRUD 操作
    todos: List[TodoItem] = []

    # Create
    print("=== CREATE ===")
    todos = create_todo(todos, "查詢 DATCOM 文檔")
    todos = create_todo(todos, "生成 DATCOM 檔案")
    todos = create_todo(todos, "驗證 DATCOM 格式")
    print_todo_list(todos)

    # Update
    print("\n=== UPDATE ===")
    todos = mark_todo_in_progress(todos, "查詢 DATCOM 文檔")
    print_todo_list(todos)

    todos = mark_todo_completed(todos, "查詢 DATCOM 文檔")
    todos = mark_todo_in_progress(todos, "生成 DATCOM 檔案")
    print_todo_list(todos)

    todos = mark_todo_failed(todos, "生成 DATCOM 檔案", "驗證失敗：缺少必要欄位")
    print_todo_list(todos)

    # Read
    print("\n=== READ ===")
    summary = get_todo_summary(todos)
    print(f"統計: {summary}")

    failed_todos = get_todos_by_status(todos, "failed")
    print(f"失敗的任務: {[t['task'] for t in failed_todos]}")

    # Delete
    print("\n=== DELETE ===")
    todos = delete_todo(todos, "驗證 DATCOM 格式")
    print_todo_list(todos)
