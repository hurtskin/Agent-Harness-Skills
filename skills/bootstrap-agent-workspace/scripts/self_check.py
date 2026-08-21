#!/usr/bin/env python3
"""Validate stable bootstrap-agent-workspace publishing contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

SKILL_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "SKILL.md",
    "COMMON.md",
    "workflows/core-documents.md",
    "workflows/verification.md",
    "modules/kanban.md",
    "modules/drift-check.md",
    "modules/python-workspace.md",
    "modules/path-align-hooks.md",
    "templates/kanban/BACKLOG.md.template",
    "templates/tools/pyproject.toml.template",
    "templates/path_align_hooks/README.md",
    "templates/path_align_hooks/drift_lite.ps1",
    "templates/path_align_hooks/drift_lite.sh",
    "templates/path_align_hooks/turn_align.ps1",
    "templates/path_align_hooks/turn_align.sh",
    "templates/drift_check/pyproject.toml",
    "templates/drift_check/src/drift_check/cli.py",
    "templates/drift_check/src/drift_check/adapters/base.py",
    "templates/drift_check/src/drift_check/detectors/common.py",
    "templates/drift_check/tests/test_d1_version.py",
)
ADAPTERS = ("claude-code",)
MODULES = ("kanban", "drift-check", "python-workspace", "path-align-hooks")
ADAPTER_HEADINGS = ("检测信号", "生成策略", "校验")
FACT_SOURCES = {
    "AGENTS.md",
    "decisions/",
    "BACKLOG.md",
}
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`]+)`")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}


def is_source_file(path: Path, root: Path) -> bool:
    return not any(part in SKIP_DIRS for part in path.relative_to(root).parts)


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file() and is_source_file(path, root))


def check_required_files(root: Path) -> list[str]:
    errors = [f"缺少关键文件: {rel}" for rel in REQUIRED_FILES if not (root / rel).is_file()]
    errors.extend(
        f"缺少适配器: adapters/{name}.md"
        for name in ADAPTERS
        if not (root / "adapters" / f"{name}.md").is_file()
    )
    return errors


def check_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for document in markdown_files(root):
        text = read_text(document)
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "/", "\\")):
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            relative = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if relative and not (document.parent / relative).resolve().exists():
                shown = document.relative_to(root).as_posix()
                errors.append(f"无效 Markdown 相对链接: {shown} -> {target}")
    return errors


def check_structure(root: Path) -> list[str]:
    errors: list[str] = []
    for name in ADAPTERS:
        path = root / "adapters" / f"{name}.md"
        if not path.is_file():
            continue
        text = read_text(path)
        for heading in ADAPTER_HEADINGS:
            if not re.search(rf"^##\s+.*{re.escape(heading)}\s*$", text, re.MULTILINE):
                errors.append(f"适配器缺少关键结构 {heading}: adapters/{name}.md")
        if name != "zcoder" and not re.search(r"^##\s+.*(?:自动加载入口|官方入口)\s*$", text, re.MULTILINE):
            errors.append(f"适配器缺少入口说明: adapters/{name}.md")
    for name in MODULES:
        path = root / "modules" / f"{name}.md"
        if not path.is_file():
            continue
        text = read_text(path)
        if not re.search(r"^##\s+.*(?:生成|目标结构)\s*$", text, re.MULTILINE):
            errors.append(f"模块缺少生成/目标结构: modules/{name}.md")
        if not re.search(r"^##\s+.*(?:验证|统一测试|职责)\s*$", text, re.MULTILINE):
            errors.append(f"模块缺少验证/职责结构: modules/{name}.md")
    return errors


def _fact_sources_from_skill(text: str) -> set[str]:
    match = re.search(r"公共项目事实只存在于\s*(.+?)。", text)
    return set(BACKTICK_RE.findall(match.group(1))) if match else set()


def _fact_sources_from_common(text: str) -> set[str]:
    match = re.search(r"##\s+1\.\s*单一事实源(?P<body>.*?)(?:\n##\s+2\.)", text, re.DOTALL)
    if not match:
        return set()
    return {value for value in BACKTICK_RE.findall(match.group("body")) if value in FACT_SOURCES}


def check_fact_sources(root: Path) -> list[str]:
    skill_sources = _fact_sources_from_skill(read_text(root / "SKILL.md"))
    common_sources = _fact_sources_from_common(read_text(root / "COMMON.md"))
    errors: list[str] = []
    if skill_sources != FACT_SOURCES:
        errors.append(f"SKILL.md 公共事实源定义漂移: {sorted(skill_sources)}")
    if common_sources != FACT_SOURCES:
        errors.append(f"COMMON.md 公共事实源定义漂移: {sorted(common_sources)}")
    return errors


def validate(root: Path) -> list[str]:
    checks = (
        check_required_files,
        check_markdown_links,
        check_structure,
        check_fact_sources,
    )
    errors: list[str] = []
    for check in checks:
        errors.extend(check(root))
    return errors


def configure_output_encoding() -> None:
    """Use UTF-8 for Chinese diagnostics on Windows and CI consoles."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    configure_output_encoding()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT, help="Skill 根目录")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"自检失败：{len(errors)} 个问题。")
        return 1
    print(f"自检通过：{root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
