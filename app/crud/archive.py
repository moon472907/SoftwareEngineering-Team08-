from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.archive import Archive

if TYPE_CHECKING:
    from app.models.page import Page


def get_archives_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 20) -> list[Archive]:
    return (
        db.query(Archive)
        .filter(Archive.page_id == page_id)
        .order_by(Archive.version.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_archive(db: Session, archive_id: int) -> Archive | None:
    return db.query(Archive).filter(Archive.id == archive_id).first()


def create_archive(db: Session, page: "Page", editor_id: int) -> Archive:
    archive = Archive(
        page_id=page.id,
        editor_id=editor_id,
        title=page.title,
        content=page.content,
        version=page.version,
    )
    db.add(archive)
    db.flush()
    return archive


# ---------------------------------------------------------------------------
# Myers Difference Algorithm — diff-based archiving (DB 미연동, 추후 사용)
# ---------------------------------------------------------------------------

@dataclass
class DiffEdit:
    """Myers diff 의 단일 편집 연산."""
    op: str          # 'equal' | 'insert' | 'delete'
    lines: list[str]


@dataclass
class DiffArchive:
    """
    전체 내용 대신 이전 버전과의 델타(diff)만 저장하는 아카이브.
    create_archive_ver2 로 생성하며, restore_from_diff_archive / revert_to_previous_version 으로 복구한다.
    """
    page_id: int
    editor_id: int
    title: str
    version: int
    diff: list[DiffEdit]
    archived_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "page_id": self.page_id,
            "editor_id": self.editor_id,
            "title": self.title,
            "version": self.version,
            "diff": [{"op": e.op, "lines": e.lines} for e in self.diff],
            "archived_at": self.archived_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> DiffArchive:
        return cls(
            page_id=data["page_id"],
            editor_id=data["editor_id"],
            title=data["title"],
            version=data["version"],
            diff=[DiffEdit(op=e["op"], lines=e["lines"]) for e in data["diff"]],
            archived_at=datetime.fromisoformat(data["archived_at"]),
        )


# --- Myers 알고리즘 내부 구현 ---

def _myers_diff(old: list[str], new: list[str]) -> list[tuple[str, str]]:
    """
    Myers Shortest Edit Script (SES) 알고리즘.
    old → new 로 변환하는 최소 편집 연산 목록을 반환한다.
    반환값: [('equal'|'insert'|'delete', line), ...]
    """
    n, m = len(old), len(new)

    if n == 0:
        return [("insert", line) for line in new]
    if m == 0:
        return [("delete", line) for line in old]

    # v[k] = 대각선 k 에서 도달 가능한 최대 x 좌표
    v: dict[int, int] = {1: 0}
    # trace[d] = d번째 편집 연산 시작 직전의 v 스냅샷
    trace: list[dict[int, int]] = []

    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            # k == -d 이면 반드시 insert(아래로 이동), k == d 이면 반드시 delete(오른쪽 이동)
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)       # insert: y만 증가
            else:
                x = v.get(k - 1, 0) + 1   # delete: x 증가
            y = x - k
            # snake: 동일한 줄은 편집 없이 대각선 이동
            while x < n and y < m and old[x] == new[y]:
                x += 1
                y += 1
            v[k] = x
            if x >= n and y >= m:
                return _backtrack(old, new, trace, d)

    return []  # 도달 불가 (이론상 발생하지 않음)


def _backtrack(
    old: list[str],
    new: list[str],
    trace: list[dict[int, int]],
    d: int,
) -> list[tuple[str, str]]:
    """Myers 알고리즘 역추적 — 편집 연산 목록을 순서대로 복원한다."""
    x, y = len(old), len(new)
    edits: list[tuple[str, str]] = []

    for cur_d in range(d, 0, -1):
        v = trace[cur_d]
        k = x - y

        # 순방향과 동일한 조건으로 이전 대각선 결정
        if k == -cur_d or (k != cur_d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1  # insert 경로
        else:
            prev_k = k - 1  # delete 경로

        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k

        # snake 구간 (equal)
        while x > prev_x and y > prev_y:
            edits.append(("equal", old[x - 1]))
            x -= 1
            y -= 1

        # 단일 편집 연산
        if prev_k == k - 1:                    # delete
            edits.append(("delete", old[x - 1]))
            x -= 1
        else:                                  # insert
            edits.append(("insert", new[y - 1]))
            y -= 1

    # 남은 공통 접두사
    while x > 0 and y > 0:
        edits.append(("equal", old[x - 1]))
        x -= 1
        y -= 1

    edits.reverse()
    return edits


def _group_edits(edits: list[tuple[str, str]]) -> list[DiffEdit]:
    """연속된 동일 연산을 하나의 DiffEdit 으로 묶는다."""
    groups: list[DiffEdit] = []
    for op, line in edits:
        if groups and groups[-1].op == op:
            groups[-1].lines.append(line)
        else:
            groups.append(DiffEdit(op=op, lines=[line]))
    return groups


# --- 공개 함수 ---

def create_archive_ver2(
    prev_content: str,
    curr_content: str,
    title: str,
    version: int,
    page_id: int,
    editor_id: int,
) -> DiffArchive:
    """
    Myers diff 를 활용한 아카이브 생성.
    전체 내용 대신 이전 버전(prev_content)과 현재 버전(curr_content)의 차이만 저장한다.
    반복 저장 시 기존 create_archive 대비 공간 효율이 높다.
    """
    prev_lines = prev_content.splitlines(keepends=True)
    curr_lines = curr_content.splitlines(keepends=True)
    raw_edits = _myers_diff(prev_lines, curr_lines)
    return DiffArchive(
        page_id=page_id,
        editor_id=editor_id,
        title=title,
        version=version,
        diff=_group_edits(raw_edits),
    )


def restore_from_diff_archive(base_content: str, diff_archives: list[DiffArchive]) -> str:
    """
    기준 버전(base_content)에 diff 아카이브를 순서대로 적용해 특정 버전을 복구한다.
    diff_archives 는 버전 오름차순(오래된 것 → 최신)으로 전달해야 한다.

    사용 예:
        v1_content = "..."          # 최초 전체 저장본
        archive_v2 = create_archive_ver2(v1_content, v2_content, ...)
        archive_v3 = create_archive_ver2(v2_content, v3_content, ...)
        restored_v3 = restore_from_diff_archive(v1_content, [archive_v2, archive_v3])
    """
    lines = base_content.splitlines(keepends=True)
    for archive in diff_archives:
        result: list[str] = []
        for edit in archive.diff:
            if edit.op in ("equal", "insert"):
                result.extend(edit.lines)
            # 'delete' 는 이전 버전에만 존재하므로 제외
        lines = result
    return "".join(lines)


def revert_to_previous_version(archive: DiffArchive) -> str:
    """
    현재 문서에 저장된 diff 를 역방향으로 적용해 이전 버전 내용을 복구한다.
    archive.diff 는 prev → curr 방향이므로, insert 를 제거하고 delete 를 복원한다.

    사용 예:
        archive = create_archive_ver2(old_content, new_content, ...)
        old_content_restored = revert_to_previous_version(archive)
    """
    result: list[str] = []
    for edit in archive.diff:
        if edit.op in ("equal", "delete"):
            result.extend(edit.lines)
        # 'insert' 는 현재 버전에서 추가된 줄이므로 이전 버전엔 없음
    return "".join(result)
