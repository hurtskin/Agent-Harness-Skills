"""L1 inventory drift + L2 regex symbol extraction (stdlib, cross-language baseline).

Usage:
  python specs/drift/drift_inventory.py --repo-root . --inventory specs/drift/pilot/inventory.yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    layer: str
    severity: str
    message: str
    evidence: dict[str, object] = field(default_factory=dict)


def _parse_scalar(val_raw: str) -> object:
    val_raw = val_raw.strip()
    if val_raw.startswith("[") and val_raw.endswith("]"):
        inner = val_raw[1:-1].strip()
        return [x.strip() for x in inner.split(",") if x.strip()] if inner else []
    return val_raw.strip('"').strip("'")


def parse_simple_yaml(path: Path) -> dict[str, object]:
    """Indent-aware minimal YAML for inventory / profiles."""
    lines: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip()), raw.strip()))

    root: dict[str, object] = {}
    stack: list[tuple[int, object]] = [(-1, root)]
    list_key_hints = frozenset({"symbols", "bindings", "members", "paths"})

    for indent, text in lines:
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if text.startswith("- "):
            content = text[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"list item under non-list at {path}: {text}")
            if ":" in content:
                key, val_raw = content.split(":", 1)
                key = key.strip()
                val_raw = val_raw.strip()
                if val_raw == "":
                    child: object = [] if key in list_key_hints else {}
                    item: dict[str, object] = {key: child}
                    parent.append(item)
                    stack.append((indent, item))
                    stack.append((indent + 1, child))
                else:
                    item = {key: _parse_scalar(val_raw)}
                    parent.append(item)
                    stack.append((indent, item))
            else:
                parent.append(_parse_scalar(content))
            continue

        if ":" not in text:
            continue
        key, val_raw = text.split(":", 1)
        key = key.strip()
        val_raw = val_raw.strip()

        if val_raw == "":
            child: object = [] if key in list_key_hints else {}
            if isinstance(parent, dict):
                parent[key] = child
            elif isinstance(parent, list) and parent and isinstance(parent[-1], dict):
                parent[-1][key] = child
            stack.append((indent, child))
        else:
            val = _parse_scalar(val_raw)
            if isinstance(parent, dict):
                parent[key] = val
            elif isinstance(parent, list) and parent and isinstance(parent[-1], dict):
                parent[-1][key] = val

    return root


def count_markdown(repo: Path, spec_md: Path, tasks_md: Path) -> dict[str, int]:
    spec_text = (repo / spec_md).read_text(encoding="utf-8")
    tasks_text = (repo / tasks_md).read_text(encoding="utf-8")
    gherkin = len(
        re.findall(r"^\s*Scenario(?:\s+Outline)?:", spec_text, re.M | re.I)
    )
    properties = len(re.findall(r"\bP-[A-Z0-9]+-\d+", spec_text))
    pt = len(re.findall(r"\bPT-[A-Z0-9]+-\d+", spec_text))
    tc = len(re.findall(r"\bTC-[A-Z0-9_-]+", tasks_text))
    return {
        "gherkin_scenarios": gherkin,
        "tc_markers": tc,
        "properties": properties,
        "pt_automated": pt,
    }


def load_profiles(path: Path) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    data = parse_simple_yaml(path)
    ext_map = data.get("extension_map", {})
    profiles = data.get("profiles", {})
    if not isinstance(ext_map, dict) or not isinstance(profiles, dict):
        raise ValueError("invalid language_profiles.yaml")
    ext_typed = {str(k): str(v) for k, v in ext_map.items()}
    prof_typed: dict[str, dict[str, str]] = {}
    for name, patterns in profiles.items():
        if isinstance(patterns, dict):
            prof_typed[str(name)] = {str(k): str(v) for k, v in patterns.items()}
    return ext_typed, prof_typed


def language_for(path: Path, ext_map: dict[str, str]) -> str | None:
    return ext_map.get(path.suffix.lower())


def extract_type_block(
    lines: list[str],
    type_name: str,
    profile: dict[str, str],
) -> set[str]:
    """Extract members for a named type using regex scan (baseline, not semantic)."""
    members: set[str] = set()
    in_type = False
    class_re = re.compile(profile.get("class", r"^\s*class\s+(\w+)"))
    struct_re = re.compile(profile.get("type_struct", r"^\s*type\s+(\w+)\s+struct"))
    enum_member_re = re.compile(profile.get("enum_member", r"^\s+(\w+)\s*="))
    field_re = re.compile(profile.get("dataclass_field", r"^\s+(\w+)\s*:"))
    struct_field_re = re.compile(profile.get("struct_field", r"^\s+(\w+)\s+\w"))

    for line in lines:
        if class_re.match(line) and class_re.match(line).group(1) == type_name:
            in_type = True
            continue
        if struct_re.match(line) and struct_re.match(line).group(1) == type_name:
            in_type = True
            continue
        if not in_type:
            continue
        if line.strip() == "" or re.match(r"^\s*@\w+", line):
            continue
        if re.match(r"^\s*(class|def|func)\s", line):
            break
        for regex in (enum_member_re, field_re, struct_field_re):
            m = regex.match(line)
            if m:
                members.add(m.group(1))
    return members


def extract_symbols_from_file(
    path: Path,
    ext_map: dict[str, str],
    profiles: dict[str, dict[str, str]],
) -> dict[str, set[str]]:
    lang = language_for(path, ext_map)
    if not lang or lang not in profiles:
        return {}
    profile = profiles[lang]
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    classes: set[str] = set()
    for line in lines:
        for key in ("class", "type_struct", "struct"):
            pat = profile.get(key)
            if pat:
                m = re.match(pat, line)
                if m:
                    classes.add(m.group(1))
    out: dict[str, set[str]] = {}
    for name in classes:
        out[name] = extract_type_block(lines, name, profile)
    return out


def check_counts(
    manifest: dict[str, int],
    live: dict[str, int],
    spec_rel: str,
) -> list[Finding]:
    findings: list[Finding] = []
    for key in sorted(manifest.keys()):
        m = manifest.get(key, 0)
        l = live.get(key, 0)
        if m != l:
            findings.append(
                Finding(
                    layer="L1",
                    severity="error",
                    message=f"count drift {key}: inventory={m} live={l}",
                    evidence={
                        "spec": spec_rel,
                        "key": key,
                        "inventory": m,
                        "live": l,
                    },
                )
            )
    return findings


def check_bindings(
    repo: Path,
    bindings: list[dict[str, object]],
    ext_map: dict[str, str],
    profiles: dict[str, dict[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for binding in bindings:
        expect = binding.get("expect", {})
        if not isinstance(expect, dict):
            continue
        type_name = str(expect.get("type_name", ""))
        expect_members = set(expect.get("members", []) if isinstance(expect.get("members"), list) else [])
        paths = binding.get("paths", [])
        if not isinstance(paths, list):
            continue
        found_members: set[str] = set()
        type_found = False
        for rel in paths:
            code_path = repo / str(rel)
            if not code_path.exists():
                findings.append(
                    Finding(
                        layer="L2",
                        severity="error",
                        message=f"missing code path for {type_name}: {rel}",
                        evidence={"path": str(rel)},
                    )
                )
                continue
            symbols = extract_symbols_from_file(code_path, ext_map, profiles)
            if type_name in symbols:
                type_found = True
                found_members |= symbols[type_name]
        if not type_found:
            findings.append(
                Finding(
                    layer="L2",
                    severity="error",
                    message=f"type not found in bindings: {type_name}",
                    evidence={"paths": paths},
                )
            )
            continue
        missing = expect_members - found_members
        extra = found_members - expect_members if expect_members else set()
        if missing:
            findings.append(
                Finding(
                    layer="L2",
                    severity="error",
                    message=f"members missing for {type_name}: {sorted(missing)}",
                    evidence={
                        "expected": sorted(expect_members),
                        "found": sorted(found_members),
                    },
                )
            )
        if extra and expect_members:
            findings.append(
                Finding(
                    layer="L2",
                    severity="warning",
                    message=f"extra members for {type_name}: {sorted(extra)}",
                    evidence={
                        "expected": sorted(expect_members),
                        "found": sorted(found_members),
                    },
                )
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="inventory drift (L1 counts + L2 symbols)")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument(
        "--profiles",
        type=Path,
        default=None,
        help="language_profiles.yaml (default: sibling of this script)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    repo = args.repo_root.resolve()
    inventory_path = args.inventory.resolve()
    profiles_path = args.profiles or Path(__file__).resolve().parent / "language_profiles.yaml"

    inv = parse_simple_yaml(inventory_path)
    sources = inv.get("sources", {})
    counts = inv.get("counts", {})
    bindings = inv.get("bindings", [])

    if not isinstance(sources, dict) or not isinstance(counts, dict):
        print("[drift] invalid inventory: sources/counts", file=sys.stderr)
        return 2

    spec_md = Path(str(sources.get("spec_md", "")))
    tasks_md = Path(str(sources.get("tasks_md", "")))
    live = count_markdown(repo, spec_md, tasks_md)
    manifest_counts = {str(k): int(v) for k, v in counts.items()}

    ext_map, profile_map = load_profiles(profiles_path)
    findings: list[Finding] = []
    findings.extend(
        check_counts(manifest_counts, live, str(sources.get("spec_md", "")))
    )
    binding_list = bindings if isinstance(bindings, list) else []
    findings.extend(
        check_bindings(
            repo,
            [b for b in binding_list if isinstance(b, dict)],
            ext_map,
            profile_map,
        )
    )

    if args.format == "json":
        print(
            json.dumps(
                [
                    {
                        "layer": f.layer,
                        "severity": f.severity,
                        "message": f.message,
                        "evidence": f.evidence,
                    }
                    for f in findings
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if not findings:
            print("[drift] OK - inventory matches live spec + code symbols")
        else:
            for f in findings:
                print(f"[{f.severity}] {f.layer}: {f.message}")
                for k, v in f.evidence.items():
                    print(f"    {k}: {v}")

    has_error = any(f.severity == "error" for f in findings)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
