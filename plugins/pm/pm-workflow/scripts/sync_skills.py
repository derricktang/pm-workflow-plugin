#!/usr/bin/env python3
"""sync_skills.py — Synchronize vendored skills from upstream sources.

Reads pm-workflow/skills/.sources.json (top-level array of source entries) and
manages the lifecycle of each source: drift detection, selective update, diff
inspection. Supports multiple upstream sources side-by-side; new source types
can be added by extending TYPE_HANDLERS.

Subcommands:
  list                                 Print all sources and their selected skills
  status [--source <id>]               Report drift between local and upstream HEAD
  update [--source <id>] [--to <ref>]  Pull upstream and overwrite selected skills
  diff <skill>                         Show diff between local and upstream HEAD
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_paths import FRAMEWORK_ROOT, PROJECT_ROOT
SKILLS_DIR = FRAMEWORK_ROOT / "pm-workflow" / "skills"
SOURCES_FILE = SKILLS_DIR / ".sources.json"


def load_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        sys.exit(f"ERROR: {SOURCES_FILE} not found")
    data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        sys.exit("ERROR: .sources.json top-level must be an array")
    return data


def save_sources(sources: list[dict]) -> None:
    SOURCES_FILE.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def upstream_head(repo: str, branch: str) -> str:
    out = run(["git", "ls-remote", repo, branch]).stdout.strip()
    if not out:
        sys.exit(f"ERROR: cannot resolve {branch} on {repo}")
    return out.split()[0]


def sparse_fetch(repo: str, ref: str, path_prefix: str, names: list[str], dest: Path) -> None:
    """Sparse-clone repo at ref, copy <path_prefix>/<name>/ into dest/<name>/ for each name."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "upstream"
        run(["git", "clone", "--no-checkout", "--filter=blob:none",
             "--sparse", repo, str(tmp_repo)])
        run(["git", "-C", str(tmp_repo), "sparse-checkout", "set", path_prefix])
        run(["git", "-C", str(tmp_repo), "checkout", ref])
        for name in names:
            src = tmp_repo / path_prefix / name
            if not src.is_dir():
                print(f"  WARN: {name} missing in upstream {ref[:8]}, skipped")
                continue
            target = dest / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
            print(f"  ✓ {name}")


def fmt_source_header(src: dict) -> str:
    if src["type"] == "git":
        return f"[{src['id']}]  git  {src['repo']}@{src['branch']}"
    return f"[{src['id']}]  {src['type']}"


def cmd_list(sources: list[dict]) -> int:
    for src in sources:
        print(fmt_source_header(src))
        if src["type"] == "git":
            commit = src.get("fetched_commit", "")
            print(f"  fetched: {commit[:8] if commit else '(none)'} ({src.get('fetched_at', '?')})")
            mods = src.get("local_modifications", {}) or {}
            selected = src.get("selected", [])
            print(f"  selected ({len(selected)}):")
            for s in selected:
                marker = "  *modified" if s in mods else ""
                print(f"    - {s}{marker}")
        elif src["type"] == "self_authored":
            skills = src.get("skills", [])
            print(f"  skills ({len(skills)}):")
            for s in skills:
                print(f"    - {s}")
        print()
    return 0


def cmd_status(sources: list[dict], source_id: str | None) -> int:
    any_drift = False
    matched = False
    for src in sources:
        if source_id and src["id"] != source_id:
            continue
        matched = True
        if src["type"] != "git":
            print(f"[{src['id']}]  {src['type']}  (no upstream to check)")
            continue
        head = upstream_head(src["repo"], src["branch"])
        local = src.get("fetched_commit", "")
        if head == local:
            print(f"[{src['id']}]  ✓ up-to-date  ({head[:8]})")
        else:
            print(f"[{src['id']}]  ✗ drift")
            print(f"    local:    {local or '(none)'}")
            print(f"    upstream: {head}")
            any_drift = True
    if source_id and not matched:
        sys.exit(f"ERROR: no source with id={source_id}")
    return 1 if any_drift else 0


def cmd_update(sources: list[dict], source_id: str | None, ref: str | None) -> int:
    changed = False
    matched = False
    for src in sources:
        if source_id and src["id"] != source_id:
            continue
        matched = True
        if src["type"] != "git":
            print(f"[{src['id']}]  {src['type']}  (skip: no upstream)")
            continue
        target_ref = ref if ref else src["branch"]
        target_commit = (
            target_ref if ref else upstream_head(src["repo"], src["branch"])
        )
        if not ref and target_commit == src.get("fetched_commit"):
            print(f"[{src['id']}]  already at {target_commit[:8]}")
            continue
        print(f"[{src['id']}]  → {target_commit[:8]}")
        skipped = list((src.get("local_modifications") or {}).keys())
        for s in skipped:
            print(f"  ⏭ {s}  (local_modifications)")
        names = [n for n in src.get("selected", []) if n not in skipped]
        sparse_fetch(src["repo"], target_commit, src["path_prefix"], names, SKILLS_DIR)
        src["fetched_commit"] = target_commit
        src["fetched_at"] = date.today().isoformat()
        changed = True
    if source_id and not matched:
        sys.exit(f"ERROR: no source with id={source_id}")
    if changed:
        save_sources(sources)
        print("\n.sources.json updated")
    return 0


def cmd_diff(sources: list[dict], skill: str) -> int:
    owner = next(
        (s for s in sources if s["type"] == "git" and skill in s.get("selected", [])),
        None,
    )
    if not owner:
        sys.exit(f"ERROR: {skill} not in any git source's selected list")
    local = SKILLS_DIR / skill
    if not local.is_dir():
        sys.exit(f"ERROR: local {local} does not exist")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "upstream"
        run(["git", "clone", "--no-checkout", "--filter=blob:none",
             "--sparse", owner["repo"], str(tmp_repo)])
        run(["git", "-C", str(tmp_repo), "sparse-checkout", "set",
             f"{owner['path_prefix']}/{skill}"])
        run(["git", "-C", str(tmp_repo), "checkout", owner["branch"]])
        upstream_skill = tmp_repo / owner["path_prefix"] / skill
        if not upstream_skill.is_dir():
            sys.exit(f"ERROR: {skill} not in upstream {owner['branch']}")
        result = subprocess.run(
            ["diff", "-r", "-u", str(local), str(upstream_skill)],
            capture_output=True, text=True
        )
        if not result.stdout:
            print(f"{skill}: no diff vs upstream {owner['branch']}")
        else:
            sys.stdout.write(result.stdout)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p_status = sub.add_parser("status")
    p_status.add_argument("--source", dest="source_id")
    p_update = sub.add_parser("update")
    p_update.add_argument("--source", dest="source_id")
    p_update.add_argument("--to", dest="ref", help="commit hash, tag, or branch (default: source branch HEAD)")
    p_diff = sub.add_parser("diff")
    p_diff.add_argument("skill")
    args = parser.parse_args()
    sources = load_sources()
    if args.cmd == "list":
        return cmd_list(sources)
    if args.cmd == "status":
        return cmd_status(sources, args.source_id)
    if args.cmd == "update":
        return cmd_update(sources, args.source_id, args.ref)
    if args.cmd == "diff":
        return cmd_diff(sources, args.skill)
    return 0


if __name__ == "__main__":
    sys.exit(main())
