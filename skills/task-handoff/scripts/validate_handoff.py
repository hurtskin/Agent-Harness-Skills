#!/usr/bin/env python3
# 确定性 handoff 状态文件验证器 (task-handoff SKILL §4.1 实现)
# 用法: python validate_handoff.py <file>
# 退出码 0 = 通过; 1 = 校验失败. 通过时 stdout 末行打印 "DIGEST <sha256>"
import sys, re, hashlib

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML 未安装\n")
    sys.exit(2)

def configure_output_encoding() -> None:
    """Use UTF-8 for Chinese diagnostics on Windows and CI consoles (L-002)."""
    for _name in ("stdout", "stderr"):
        _stream = getattr(sys, _name)
        _reconfigure = getattr(_stream, "reconfigure", None)
        if _reconfigure is not None:
            _reconfigure(encoding="utf-8", errors="backslashreplace")

ALLOWED_TOP = {"schema_version","session_id","repository","branch","base_commit",
               "working_tree","handoff_status","interrogation_round","last_audit_status",
               "status_reason","status_evidence","created_at","updated_at"}
ALLOWED_EV = {"kind","ref","claim","verification"}
WORKING_TREE = {"CLEAN","DIRTY","UNAVAILABLE"}
HANDOFF_STATUS = {"COLLECTING","NEEDS_ANSWERS","REVIEW_PENDING","READY","READY_WITH_RISKS","BLOCKED"}
KIND_ENUM = {"source","document","test","diff","commit","command","unverified"}
VERIF_ENUM = {"VERIFIED","UNVERIFIED"}
LAST_AUDIT = {"READY","READY_WITH_RISKS","NEEDS_ANSWERS","BLOCKED"}
TLDR_SECTIONS = ["Objective","Current State","Next Action","Blockers and Risks",
                 "Critical Constraints","Evidence Anchors"]
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
HEX = re.compile(r"^[0-9a-fA-F]{7,64}$")

errors = []

def ok(cond, msg):
    if not cond: errors.append(msg)

class DupKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        seen = set()
        for k_node, _ in node.value:
            try:
                k = self.construct_object(k_node, deep=deep)
            except Exception:
                k = repr(k_node)
            if k in seen:
                raise ValueError(f"重复键: {k}")
            seen.add(k)
        return super().construct_mapping(node, deep)

def reject_anchors_aliases(text):
    # 扫描顶层 YAML 块中的锚点 & 和别名 *
    for m in re.finditer(r"(^|\n)\s*([&*]\w+)", text):
        errors.append(f"YAML 锚点/别名被拒绝: {m.group(2)}")

def main():
    configure_output_encoding()
    if len(sys.argv) != 2:
        sys.stderr.write("用法: validate_handoff.py <file>\n"); sys.exit(2)
    path = sys.argv[1]
    raw = open(path, "rb").read()
    # 1. UTF-8 可解码
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        sys.stderr.write(f"UTF-8 解码失败: {e}\n"); sys.exit(1)

    # 2. Front Matter 提取
    if not text.startswith("---\n"):
        sys.stderr.write("缺少 Front Matter 起始 ---\n"); sys.exit(1)
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        sys.stderr.write("Front Matter 未闭合\n"); sys.exit(1)
    yaml_text = parts[1]
    body = parts[2]

    # 3. 安全 YAML 解析 (禁任意构造/自定义标签/外部引用; 拒重复键/锚点别名/多文档)
    reject_anchors_aliases(yaml_text)
    docs = list(yaml.compose_all(yaml_text, Loader=DupKeyLoader))
    if len(docs) != 1:
        errors.append(f"多文档输入被拒绝 (检出 {len(docs)} 个)")
    if errors:
        for e in errors: sys.stderr.write(e + "\n"); sys.exit(1)
    try:
        data = yaml.load(yaml_text, Loader=DupKeyLoader)
    except ValueError as e:
        sys.stderr.write(f"YAML 安全解析失败: {e}\n"); sys.exit(1)
    except yaml.YAMLError as e:
        sys.stderr.write(f"YAML 解析失败: {e}\n"); sys.exit(1)
    if not isinstance(data, dict):
        sys.stderr.write("Front Matter 不是映射\n"); sys.exit(1)

    # 4. 顶层字段集合严格相等
    keys = set(data.keys())
    ok(keys == ALLOWED_TOP, f"顶层字段集合不匹配: 多 {keys-ALLOWED_TOP} 少 {ALLOWED_TOP-keys}")

    # 5. 类型/非空/枚举校验
    ok(isinstance(data.get("schema_version"), int) and data["schema_version"]==2,
       "schema_version 必须为整数 2")
    ok(isinstance(data.get("session_id"),str) and data["session_id"].strip()!="",
       "session_id 非空字符串")
    ok(isinstance(data.get("repository"),str) and data["repository"].strip()!="",
       "repository 非空字符串")
    ok(data.get("branch") is None or isinstance(data.get("branch"),str),
       "branch 为 string|null")
    bc = data.get("base_commit")
    ok(bc is None or (isinstance(bc,str) and HEX.match(bc)),
       "base_commit 为 null 或 7-64 位十六进制")
    ok(data.get("working_tree") in WORKING_TREE, "working_tree 枚举非法")
    ok(data.get("handoff_status") in HANDOFF_STATUS, "handoff_status 枚举非法")
    ok(isinstance(data.get("interrogation_round"),int) and 0<=data["interrogation_round"]<=3,
       "interrogation_round 为 0..3 整数")
    la = data.get("last_audit_status")
    ok(la is None or la in LAST_AUDIT, "last_audit_status 枚举非法")
    ok(isinstance(data.get("status_reason"),str) and data["status_reason"].strip()!="",
       "status_reason 非空")
    ok(isinstance(data.get("status_evidence"),list) and len(data["status_evidence"])>0,
       "status_evidence 非空数组")
    ok(RFC3339.match(data.get("created_at","") or "") is not None, "created_at 非 RFC3339")
    ok(RFC3339.match(data.get("updated_at","") or "") is not None, "updated_at 非 RFC3339")
    # updated_at 不早于 created_at
    try:
        if data.get("created_at") and data.get("updated_at") and data["updated_at"] < data["created_at"]:
            errors.append("updated_at 早于 created_at")
    except Exception: pass

    # 6. status_evidence 元素字段
    if isinstance(data.get("status_evidence"), list):
        only_unverified = (len(data["status_evidence"])==1)
        for i, ev in enumerate(data["status_evidence"]):
            if not isinstance(ev, dict):
                errors.append(f"evidence[{i}] 非映射"); continue
            ek = set(ev.keys())
            ok(ek == ALLOWED_EV, f"evidence[{i}] 字段集合不匹配: 多 {ek-ALLOWED_EV} 少 {ALLOWED_EV-ek}")
            ok(ev.get("kind") in KIND_ENUM, f"evidence[{i}].kind 枚举非法")
            ok(ev.get("ref") is None or isinstance(ev.get("ref"),str), f"evidence[{i}].ref 类型非法")
            ok(isinstance(ev.get("claim"),str) and ev["claim"].strip()!="", f"evidence[{i}].claim 非空")
            ok(ev.get("verification") in VERIF_ENUM, f"evidence[{i}].verification 枚举非法")
            if only_unverified:
                ok(ev.get("kind")=="unverified" and ev.get("ref") is None
                   and ev.get("verification")=="UNVERIFIED",
                   "唯一 evidence 元素必须为 unverified/null/UNVERIFIED")

    # 7. 交叉不变量: TL;DR Status 与 handoff_status 一致
    ok(body.lstrip().startswith("# TL;DR"), "YAML 后首标题必须为 # TL;DR")
    # 1500 Unicode 字符限制
    tldr_end = body.find("\n# ", 1)
    tldr_block = body[:tldr_end] if tldr_end != -1 else body
    ok(len(tldr_block) <= 1500, f"TL;DR 超过 1500 Unicode 字符 ({len(tldr_block)})")
    # Status 行与 handoff_status 一致
    st = data.get("handoff_status")
    m = re.search(r"Status:\s*(\S+)", tldr_block)
    if m:
        ok(m.group(1) == st, f"TL;DR Status ({m.group(1)}) 与 handoff_status ({st}) 不一致")
    else:
        errors.append("TL;DR 缺少 Status: 行")
    # 六节标题存在 (顺序宽松检查)
    pos = 0
    for sec in TLDR_SECTIONS:
        idx = tldr_block.find(f"## {sec}")
        ok(idx != -1, f"TL;DR 缺少 ## {sec}")
        ok(idx >= pos, f"TL;DR ## {sec} 顺序错误")
        pos = idx

    if errors:
        for e in errors: sys.stderr.write(e + "\n")
        sys.exit(1)
    digest = hashlib.sha256(raw).hexdigest()
    print("VALID")
    print(f"DIGEST {digest}")
    sys.exit(0)

if __name__ == "__main__":
    main()
