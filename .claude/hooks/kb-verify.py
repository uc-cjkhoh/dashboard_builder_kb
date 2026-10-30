#!/usr/bin/env python3
"""PostToolUse hook: verify an edited KB doc against docs/conventions/kb-maintenance.md.

Reads the hook JSON on stdin. If the edited file is a markdown doc of this KB (not the exempt
archive/ or a git-ignored *.local.md), it checks:
  - CLAUDE.md / README.md < 200 lines; every other doc <= 300 lines
  - ARCHITECTURE.md has no code blocks (fences with a language tag; untagged plain-text fences are allowed)
  - kebab-case filename under docs/
  - no changelog / history phrasing ("current state, not history")
  - relative links (file and #anchor) in the file resolve, and links elsewhere to this file still resolve
Findings go back to the model as additionalContext (non-blocking). Clean edits print nothing.
Run with --all to check every KB doc from the shell (prints findings, exit 1 if any).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXEMPT = ("archive/", "docs/updates/")  # updates/ is a generated log (update-log.py): history by design, underscore names
HISTORY = [
    (r"\bCorrection,? same day\b", "changelog-style 'Correction, same day'"),
    (r"\b(shipped|added|fixed|removed|changed|built|deployed|migrated)\s+(on\s+|live\s+)?\d{4}-\d{2}-\d{2}\b", "dated changelog entry"),
    (r"\b\d+(st|nd|rd|th)\s+build pass\b", "'Nth build pass'"),
    (r"\bwas\s+[^.\n]{1,40}?,\s*now\s+", "'was X, now Y' history"),
    (r"✅\s*Shipped", "'✅ Shipped' phase log"),
    (r"\*\*Built \(P\d+\)", "'Built (Pn)' build-log callout"),
]

def exempt(rel):
    return rel.startswith(EXEMPT) or rel.endswith(".local.md")

def slug(heading):
    s = re.sub(r"[`*_]", "", heading.strip().lower())
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")

def anchors(path):
    out, fence = set(), False
    try:
        for line in open(path, encoding="utf-8"):
            if line.lstrip().startswith("```"): fence = not fence
            if fence: continue
            out.update(re.findall(r'<a\s+(?:id|name)="([^"]+)"', line))      # explicit anchors
            m = re.match(r"#{1,6}\s+(.*)", line)
            if m: out.add(slug(re.sub(r"<[^>]+>", "", m.group(1))))
    except OSError:
        pass
    return out

def links(path):
    fence = False
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.lstrip().startswith("```"): fence = not fence; continue
        if fence: continue
        for m in re.finditer(r"\]\(([^)\s]+)\)", re.sub(r"`[^`]*`", "", line)):
            t = m.group(1)
            if re.match(r"[a-z]+:|//", t): continue
            yield n, t

def check_link(src, target):
    file_part, _, frag = target.partition("#")
    dest = os.path.normpath(os.path.join(os.path.dirname(src), file_part)) if file_part else src
    if not os.path.exists(dest): return f"missing file {file_part}", dest
    if frag and dest.endswith(".md") and frag not in anchors(dest): return f"missing anchor #{frag} in {os.path.relpath(dest, ROOT)}", dest
    return None, dest

def kb_docs():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in (".git", "node_modules", ".claude")]
        for fn in fns:
            p = os.path.join(dp, fn)
            if fn.endswith(".md") and not exempt(os.path.relpath(p, ROOT)):
                yield p

def check(f, inbound=True):
    rel = os.path.relpath(f, ROOT)
    text = open(f, encoding="utf-8").read()
    lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    name, issues = os.path.basename(f), []

    if rel in ("CLAUDE.md", "README.md"):
        if lines >= 200: issues.append(f"{rel} is {lines} lines; indexes must stay under 200 — move detail into docs/")
    elif lines > 300:
        issues.append(f"{rel} is {lines} lines (limit ~300) — extract its most self-contained sub-topic into a new file in the same docs/ subfolder and link it")
    # a fence with a language tag is code; an untagged fence is plain text (diagrams, trees) and allowed
    if rel == "ARCHITECTURE.md" and re.search(r"^[ \t]*```[ \t]*\w", text, re.M):
        issues.append("ARCHITECTURE.md must be high-level flow only: remove code blocks and point to source / docs/ files")
    if rel.startswith("docs/") and name != "README.md" and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*\.md", name):
        issues.append(f"filename '{name}' is not kebab-case")
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"): fence = not fence
        if fence: continue
        for pat, label in ([] if rel == "docs/conventions/kb-maintenance.md" else HISTORY):   # that page quotes the banned phrases
            if re.search(pat, line, re.I):
                issues.append(f"{rel}:{n} {label} — KB tracks current state, not history; overwrite the line instead")
    for n, t in links(f):
        err, _ = check_link(f, t)
        if err: issues.append(f"{rel}:{n} broken link ({t}): {err}")
    if inbound:   # links from other docs to this one (moved/renamed file, renamed heading)
        for p in kb_docs():
            if p == f: continue
            try:
                for n, t in links(p):
                    if os.path.normpath(os.path.join(os.path.dirname(p), t.partition("#")[0])) == f and check_link(p, t)[0]:
                        issues.append(f"{os.path.relpath(p, ROOT)}:{n} inbound link ({t}) no longer resolves: {check_link(p, t)[0]}")
            except OSError:
                pass
    return issues

def main():
    if "--all" in sys.argv:
        issues = [i for p in sorted(kb_docs()) for i in check(p, inbound=False)]
        print("\n".join(issues) if issues else "KB clean.")
        sys.exit(1 if issues else 0)
    try: data = json.load(sys.stdin)
    except Exception: return
    f = (data.get("tool_input") or {}).get("file_path") or (data.get("tool_response") or {}).get("filePath")
    if not f: return
    f = os.path.abspath(f)
    if not f.startswith(ROOT + os.sep) or not f.endswith(".md") or not os.path.exists(f): return
    if exempt(os.path.relpath(f, ROOT)): return
    issues = check(f)
    if issues:
        msg = ("KB check (docs/conventions/kb-maintenance.md) failed for " + os.path.relpath(f, ROOT) + ":\n- "
               + "\n- ".join(issues[:15]) + "\nFix these in the same change.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))

main()
