from __future__ import annotations

from model.memo import Memo
from model.task import Task


def _clip(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def build_qa_context(
    tasks: list[Task],
    memos: list[Memo],
    *,
    include_tasks: bool,
    include_memos: bool,
    task_limit: int = 24,
    memo_limit: int = 12,
) -> str:
    parts: list[str] = []
    if include_tasks:
        pending = [task for task in tasks if not task.is_completed][:task_limit]
        done = [task for task in tasks if task.is_completed][:8]
        if pending:
            lines = []
            for task in pending:
                due = task.due_label()
                extra = f"（{due}）" if due else ""
                lines.append(f"- {task.title}{extra}")
            parts.append("未完成待办：\n" + "\n".join(lines))
        if done:
            parts.append("最近已完成：\n" + "\n".join(f"- {task.title}" for task in done))
        if not pending and not done:
            parts.append("待办：暂无")
    if include_memos:
        items = memos[:memo_limit]
        if items:
            lines = []
            for memo in items:
                body = _clip(memo.content, 80)
                lines.append(f"- {memo.display_title()}：{body}" if body else f"- {memo.display_title()}")
            parts.append("备忘：\n" + "\n".join(lines))
        else:
            parts.append("备忘：暂无")
    return "\n\n".join(parts)
