#!/usr/bin/env python3
"""仓库级 Markdown 相对链接校验。

覆盖两类本地磁盘检查抓不到的死链：
- 目标磁盘缺失；
- 目标磁盘存在但被 .gitignore 忽略（发布到远端后会 404）。

只扫描发布文档：根级 *.md + skills/ + docs/，跳过本地沙箱与工具目录
（.git / .cursor / .trae / 根 tools/ / 根 specs/ / __pycache__ 等）。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]

# 匹配 [text](url) 与 ![alt](url)；标题段由后续 split 取首段处理。
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# 顶层目录跳过（本地沙箱 / 工具 / 已删体系残留），不影响 skills/spec-writing/tools/。
TOP_SKIP = {".git", ".cursor", ".trae", ".hypothesis", "tools", "specs"}
# 任意层级的垃圾目录。
JUNK_PARTS = {
    "__pycache__", ".venv", ".pytest_cache",
    ".ruff_cache", ".mypy_cache", ".git",
}


def is_publish_doc(path: Path) -> bool:
    parts = path.relative_to(REPO_ROOT).parts
    if not parts:
        return False
    if parts[0] in TOP_SKIP:
        return False
    return not any(part in JUNK_PARTS for part in parts)


def publish_docs() -> list[Path]:
    return sorted(
        path for path in REPO_ROOT.rglob("*.md")
        if path.is_file() and is_publish_doc(path)
    )


def is_gitignored(path: Path) -> bool:
    """返回 True 当且仅当该路径被本仓库 .gitignore 命中。"""
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return False  # 仓库外，本仓库规则不会忽略。
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(rel)],
            cwd=REPO_ROOT,
            capture_output=True,
        )
    except FileNotFoundError:
        return False  # 无 git 可用时降级为不忽略。
    return result.returncode == 0


def check_links() -> list[str]:
    errors: list[str] = []
    for document in publish_docs():
        text = document.read_text(encoding="utf-8-sig")
        shown = document.relative_to(REPO_ROOT).as_posix()
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "/", "\\")):
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            relative = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not relative:
                continue
            resolved = (document.parent / relative).resolve()
            if not resolved.exists():
                errors.append(f"无效链接（目标缺失）: {shown} -> {target}")
                continue
            if is_gitignored(resolved):
                errors.append(
                    f"无效链接（目标被 gitignore，发布后 404）: {shown} -> {target}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    errors = check_links()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"链接检查失败：{len(errors)} 个问题。")
        return 1
    print(f"链接检查通过：{REPO_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
