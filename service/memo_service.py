from __future__ import annotations

from datetime import datetime

from database.memo_repository import MemoRepository
from model.memo import Memo


class MemoService:
    def __init__(self, repository: MemoRepository):
        self._repo = repository

    def list_memos(self) -> list[Memo]:
        return self._repo.list_all()

    def add_memo(
        self,
        content: str,
        title: str = "",
        category: str = "工作",
        tags: str = "",
        include_in_report: bool = True,
        task_id: int | None = None,
    ) -> Memo:
        content = content.strip()
        if not content:
            raise ValueError("备忘内容不能为空")
        memo = Memo(
            content=content,
            title=title.strip(),
            category=category,
            tags=tags,
            include_in_report=include_in_report,
            task_id=task_id,
            created_at=datetime.now(),
        )
        return self._repo.add(memo)

    def update_memo(self, memo: Memo) -> Memo:
        memo.content = memo.content.strip()
        if not memo.content:
            raise ValueError("备忘内容不能为空")
        return self._repo.update(memo)

    def delete_memo(self, memo_id: int) -> None:
        self._repo.delete(memo_id)

    def set_pinned(self, memo: Memo, pinned: bool) -> Memo:
        memo.is_pinned = pinned
        return self.update_memo(memo)

    def set_include_in_report(self, memo: Memo, include: bool) -> Memo:
        memo.include_in_report = include
        return self.update_memo(memo)

    def list_for_task(self, task_id: int) -> list[Memo]:
        return [memo for memo in self.list_memos() if memo.task_id == task_id]

    def search(self, keyword: str) -> list[Memo]:
        key = keyword.strip().lower()
        memos = self.list_memos()
        if not key:
            return memos
        return [
            memo
            for memo in memos
            if key in f"{memo.title} {memo.content} {memo.tags} {memo.category}".lower()
        ]
