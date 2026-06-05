from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.archive import Archive

if TYPE_CHECKING:
    from app.models.page import Page


# ---------------------------------------------------------------------------
# DB 조회 함수
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Method 1: 전체 내용 저장
# ---------------------------------------------------------------------------

def create_archive(db: Session, page: "Page", editor_id: int) -> Archive:
    """페이지의 현재 내용을 통째로 저장한다."""
    archive = Archive(
        page_id=page.id,
        editor_id=editor_id,
        title=page.title,
        content=page.content,
        diff_data=None,
        version=page.version,
    )
    db.add(archive)
    db.flush()
    return archive


# ---------------------------------------------------------------------------
# Myers Difference Algorithm
# ---------------------------------------------------------------------------

@dataclass
class DiffEdit:
    """Myers diff 의 단일 편집 연산."""
    op: str           # 'equal' | 'insert' | 'delete'
    lines: list[str]


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

    v: dict[int, int] = {1: 0}
    trace: list[dict[int, int]] = []

    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1
            y = x - k
            while x < n and y < m and old[x] == new[y]:
                x += 1
                y += 1
            v[k] = x
            if x >= n and y >= m:
                return _backtrack(old, new, trace, d)

    return []


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

        if k == -cur_d or (k != cur_d and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:
            edits.append(("equal", old[x - 1]))
            x -= 1
            y -= 1

        if prev_k == k - 1:
            edits.append(("delete", old[x - 1]))
            x -= 1
        else:
            edits.append(("insert", new[y - 1]))
            y -= 1

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


# ---------------------------------------------------------------------------
# Method 2 독립 함수 (DB 미사용, DiffArchive 객체 반환)
# ---------------------------------------------------------------------------

@dataclass
class DiffArchive:
    """
    전체 내용 대신 이전 버전과의 델타(diff)만 보관하는 중간 객체.
    DB 저장 없이 메모리 내에서 diff를 다룰 때 사용한다.
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


def compute_diff(prev_content: str, curr_content: str) -> list[DiffEdit]:
    """두 텍스트 사이의 Myers diff를 계산해 DiffEdit 목록으로 반환한다."""
    return _group_edits(
        _myers_diff(
            prev_content.splitlines(keepends=True),
            curr_content.splitlines(keepends=True),
        )
    )


def compute_diff_compact(prev_content: str, curr_content: str) -> list[dict]:
    """
    Myers diff를 계산해 변경 부분만 담은 hunk 목록으로 반환한다.
    equal 라인을 저장하지 않으므로 공간 효율이 높다.

    반환 형식:
        [{"old_start": int, "delete_count": int, "new_lines": [str, ...]}, ...]
        - old_start   : 이전 버전 기준 변경 시작 줄 번호 (0-indexed)
        - delete_count: 이전 버전에서 제거할 줄 수
        - new_lines   : 새 버전에 삽입할 줄 목록
    """
    prev_lines = prev_content.splitlines(keepends=True)
    curr_lines = curr_content.splitlines(keepends=True)
    groups = _group_edits(_myers_diff(prev_lines, curr_lines))

    hunks: list[dict] = []
    old_pos = 0
    i = 0

    while i < len(groups):
        g = groups[i]
        if g.op == "equal":
            old_pos += len(g.lines)
            i += 1
            continue

        # 연속된 delete/insert를 하나의 hunk로 묶음
        delete_lines: list[str] = []
        insert_lines: list[str] = []
        while i < len(groups) and groups[i].op in ("delete", "insert"):
            if groups[i].op == "delete":
                delete_lines.extend(groups[i].lines)
            else:
                insert_lines.extend(groups[i].lines)
            i += 1

        hunks.append({
            "old_start": old_pos,
            "delete_count": len(delete_lines),
            "new_lines": insert_lines,
        })
        old_pos += len(delete_lines)

    return hunks


def apply_hunks(lines: list[str], hunks: list[dict]) -> list[str]:
    """
    hunk 목록을 이전 버전의 줄 목록에 적용해 새 버전을 반환한다.
    hunks는 old_start 오름차순(앞→뒤)으로 전달해야 한다.
    """
    result = list(lines)
    offset = 0
    for hunk in hunks:
        pos = hunk["old_start"] + offset
        del result[pos: pos + hunk["delete_count"]]
        for j, line in enumerate(hunk["new_lines"]):
            result.insert(pos + j, line)
        offset += len(hunk["new_lines"]) - hunk["delete_count"]
    return result


def create_archive_ver2(
    prev_content: str,
    curr_content: str,
    title: str,
    version: int,
    page_id: int,
    editor_id: int,
) -> DiffArchive:
    """Myers diff를 계산해 DiffArchive 객체로 반환한다 (DB 저장 없음)."""
    return DiffArchive(
        page_id=page_id,
        editor_id=editor_id,
        title=title,
        version=version,
        diff=compute_diff(prev_content, curr_content),
    )


def restore_from_diff_archive(base_content: str, diff_archives: list[DiffArchive]) -> str:
    """
    기준 버전(base_content)에 DiffArchive를 순서대로 적용해 특정 버전을 복원한다.
    diff_archives 는 버전 오름차순으로 전달해야 한다.
    """
    for archive in diff_archives:
        result: list[str] = []
        for edit in archive.diff:
            if edit.op in ("equal", "insert"):
                result.extend(edit.lines)
        base_content = "".join(result)
    return base_content


def revert_to_previous_version(archive: DiffArchive) -> str:
    """
    diff를 역방향으로 적용해 이전 버전 내용을 복원한다.
    (insert 제거, delete 복원)
    """
    result: list[str] = []
    for edit in archive.diff:
        if edit.op in ("equal", "delete"):
            result.extend(edit.lines)
    return "".join(result)


# ---------------------------------------------------------------------------
# Method 2 DB 연동 함수
# ---------------------------------------------------------------------------

def reconstruct_content(db: Session, page_id: int, target_version: int) -> str:
    """
    target_version 시점의 페이지 내용을 DB 아카이브 체인에서 복원한다.
    가장 최근 base 아카이브(전체 내용)를 찾은 뒤 이후 diff를 순서대로 적용한다.
    """
    archives = (
        db.query(Archive)
        .filter(Archive.page_id == page_id, Archive.version <= target_version)
        .order_by(Archive.version.asc())
        .all()
    )

    if not archives:
        return ""

    # 가장 최근 base 아카이브 위치 탐색
    base_idx = None
    for i, arch in enumerate(archives):
        if arch.content is not None:
            base_idx = i

    if base_idx is None:
        return ""

    content = archives[base_idx].content

    for arch in archives[base_idx + 1:]:
        if arch.diff_data is None:
            content = arch.content or ""
            continue
        lines = content.splitlines(keepends=True)
        lines = apply_hunks(lines, json.loads(arch.diff_data))
        content = "".join(lines)

    return content


def create_archive_v2_db(
    db: Session, page: "Page", editor_id: int, memo: str | None = None
) -> Archive:
    """
    Method 2: Myers diff를 DB에 저장하는 아카이브.
    - 첫 번째 아카이브: 전체 내용(base)을 content 컬럼에 저장
    - 이후 아카이브: 이전 버전과의 Myers diff를 diff_data 컬럼에 JSON으로 저장

    memo: 이번 수정에 대한 편집 요약(선택). 교체되는 버전의 아카이브에 함께 보관한다.
    """
    prev_archive = (
        db.query(Archive)
        .filter(Archive.page_id == page.id)
        .order_by(Archive.version.desc())
        .first()
    )

    if prev_archive is None:
        # 첫 번째 아카이브: base 전체 내용 저장
        archive = Archive(
            page_id=page.id,
            editor_id=editor_id,
            title=page.title,
            content=page.content,
            diff_data=None,
            version=page.version,
            memo=memo,
        )
    else:
        # 이전 버전 복원 후 compact hunk diff 계산
        prev_content = reconstruct_content(db, page.id, prev_archive.version)
        hunks = compute_diff_compact(prev_content, page.content)
        archive = Archive(
            page_id=page.id,
            editor_id=editor_id,
            title=page.title,
            content=None,
            diff_data=json.dumps(hunks, ensure_ascii=False),
            version=page.version,
            memo=memo,
        )

    db.add(archive)
    db.flush()
    return archive
