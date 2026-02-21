#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCENARIO_KEY = "duplicate-exports"
SKILL_NAME = "knip-detect-duplicate-exports"
IMPORT_MARKER = "// knip-scenario-import"

SCENARIOS: Dict[str, Dict[str, object]] = {
    "unused-files": {
        "expected_issue": "unused files",
        "include_type": "files",
        "issue_keys": ["files"],
        "target_subdir": "unused-files",
        "entry_file": None,
        "scope": "target_root",
    },
    "unused-dependencies": {
        "expected_issue": "unused devdependencies",
        "include_type": "dependencies",
        "issue_keys": ["dependencies", "devDependencies", "optionalPeerDependencies"],
        "target_subdir": "unused-dependencies",
        "entry_file": None,
        "scope": "package_json",
    },
    "unused-exports": {
        "expected_issue": "unused exports",
        "include_type": "exports",
        "issue_keys": ["exports"],
        "target_subdir": "unused-exports",
        "entry_file": "lib.js",
        "scope": "target_root",
    },
    "unlisted-dependencies": {
        "expected_issue": "unlisted dependencies",
        "include_type": "unlisted",
        "issue_keys": ["unlisted"],
        "target_subdir": "unlisted-dependencies",
        "entry_file": "use-dayjs.js",
        "scope": "target_root",
    },
    "unlisted-binaries": {
        "expected_issue": "unlisted binaries",
        "include_type": "binaries",
        "issue_keys": ["binaries"],
        "target_subdir": "unlisted-binaries",
        "entry_file": None,
        "scope": "package_json",
    },
    "unresolved-imports": {
        "expected_issue": "unresolved imports",
        "include_type": "unresolved",
        "issue_keys": ["unresolved"],
        "target_subdir": "unresolved-imports",
        "entry_file": "broken-import.js",
        "scope": "target_root",
    },
    "duplicate-exports": {
        "expected_issue": "duplicate exports",
        "include_type": "duplicates",
        "issue_keys": ["duplicates"],
        "target_subdir": "duplicate-exports",
        "entry_file": "index.js",
        "scope": "target_root",
    },
    "unused-exported-types": {
        "expected_issue": "unused exported types",
        "include_type": "types",
        "issue_keys": ["types"],
        "target_subdir": "unused-exported-types",
        "entry_file": "types.ts",
        "scope": "target_root",
    },
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_target_root(arg: Optional[str], subdir: str) -> Path:
    root = repo_root()
    if arg:
        target = Path(arg)
        if not target.is_absolute():
            target = root / target
        return target
    return root / "src" / "knip-lab" / subdir


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_lockfile() -> None:
    proc = subprocess.run(
        ["npm", "install", "--package-lock-only", "--ignore-scripts"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print("[warn] Failed to sync package-lock.json. Run manually if needed:")
        print("       npm install --package-lock-only --ignore-scripts")
        if proc.stderr:
            print(proc.stderr.strip())


def update_main_import(entry_file: Optional[str], subdir: str, add: bool) -> bool:
    if not entry_file:
        return False

    main_path = repo_root() / "src" / "main.jsx"
    import_line = "import './knip-lab/{}/{}'; {}\n".format(subdir, entry_file, IMPORT_MARKER)
    current = main_path.read_text(encoding="utf-8")

    if add:
        if import_line not in current:
            main_path.write_text(import_line + current, encoding="utf-8")
            return True
        return False

    if import_line in current:
        main_path.write_text(current.replace(import_line, ""), encoding="utf-8")
        return True
    return False


def apply_scenario_create(key: str, target_root: Path, changed: List[Path]) -> None:
    root = repo_root()
    subdir = str(SCENARIOS[key]["target_subdir"])

    if key == "unused-files":
        p = target_root / "orphan.js"
        write_file(p, "export const orphanValue = 'knip-unused-file';\n")
        changed.append(p)
        return

    if key == "unused-exports":
        p = target_root / "lib.js"
        write_file(p, "export function unusedFn() {\n  return 'knip-unused-export';\n}\n")
        changed.append(p)

    elif key == "unlisted-dependencies":
        p = target_root / "use-dayjs.js"
        write_file(p, "import dayjs from 'dayjs';\n\nexport const formatNow = () => dayjs().format();\n")
        changed.append(p)

    elif key == "unresolved-imports":
        p = target_root / "broken-import.js"
        write_file(p, "import { missingValue } from './not-found.js';\n\nexport const unresolvedValue = missingValue;\n")
        changed.append(p)

    elif key == "duplicate-exports":
        a = target_root / "a.js"
        b = target_root / "b.js"
        i = target_root / "index.js"
        write_file(a, "export const duplicated = 'from-a';\n")
        write_file(b, "export const duplicated = 'from-b';\n")
        write_file(i, "const duplicated = 'value';\nexport { duplicated };\nexport { duplicated };\n")
        changed.extend([a, b, i])

    elif key == "unused-exported-types":
        p = target_root / "types.ts"
        write_file(p, "export type UnusedType = {\n  id: string;\n  value: number;\n};\n")
        changed.append(p)

    elif key == "unused-dependencies":
        pkg = root / "package.json"
        data = load_json(pkg)
        dev = data.setdefault("devDependencies", {})
        if "left-pad" not in dev:
            dev["left-pad"] = "^1.3.0"
            save_json(pkg, data)
            changed.append(pkg)
            sync_lockfile()
        return

    elif key == "unlisted-binaries":
        pkg = root / "package.json"
        data = load_json(pkg)
        scripts = data.setdefault("scripts", {})
        marker = "knip:scenario:unlisted-binary"
        if marker not in scripts:
            scripts[marker] = "tsx --version"
            save_json(pkg, data)
            changed.append(pkg)
        return

    if update_main_import(SCENARIOS[key]["entry_file"], subdir, add=True):
        changed.append(root / "src" / "main.jsx")


def apply_scenario_cleanup(key: str, target_root: Path, changed: List[Path]) -> None:
    root = repo_root()
    subdir = str(SCENARIOS[key]["target_subdir"])

    if key in {
        "unused-files",
        "unused-exports",
        "unlisted-dependencies",
        "unresolved-imports",
        "duplicate-exports",
        "unused-exported-types",
    }:
        if update_main_import(SCENARIOS[key]["entry_file"], subdir, add=False):
            changed.append(root / "src" / "main.jsx")
        if target_root.exists():
            shutil.rmtree(target_root)
            changed.append(target_root)
        return

    pkg = root / "package.json"
    data = load_json(pkg)

    if key == "unused-dependencies":
        dev = data.get("devDependencies", {})
        if "left-pad" in dev:
            del dev["left-pad"]
            save_json(pkg, data)
            changed.append(pkg)
            sync_lockfile()
        return

    if key == "unlisted-binaries":
        scripts = data.get("scripts", {})
        marker = "knip:scenario:unlisted-binary"
        if marker in scripts:
            del scripts[marker]
            save_json(pkg, data)
            changed.append(pkg)
        return


def extract_json(stdout: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    return {}


def summarize_matches(data: dict, scenario: Dict[str, object], target_root: Path) -> Tuple[int, List[str]]:
    include_type = str(scenario["include_type"])
    issue_keys = [str(k) for k in scenario["issue_keys"]]
    scope = str(scenario["scope"])

    matches: List[str] = []

    if include_type == "files":
        for file_path in data.get("files", []):
            if scope == "target_root":
                abs_file = repo_root() / file_path
                if not str(abs_file).startswith(str(target_root)):
                    continue
            matches.append(str(file_path))
        return len(matches), matches

    for issue in data.get("issues", []):
        file_path = issue.get("file", "(unknown)")
        if scope == "target_root" and file_path != "(unknown)":
            abs_file = repo_root() / file_path
            if not str(abs_file).startswith(str(target_root)):
                continue

        for key in issue_keys:
            entries = issue.get(key, [])
            if not isinstance(entries, list):
                continue
            for item in entries:
                if isinstance(item, dict):
                    name = item.get("name", "(unknown)")
                    line = item.get("line")
                    if line is None:
                        matches.append("{} @ {}".format(name, file_path))
                    else:
                        matches.append("{} @ {}:{}".format(name, file_path, line))
                else:
                    matches.append("{} @ {}".format(item, file_path))

    return len(matches), matches


def line_preview(path: Path, center_line: Optional[int] = None, radius: int = 3, max_lines: int = 40) -> List[str]:
    content = path.read_text(encoding="utf-8").splitlines()
    total = len(content)

    if total == 0:
        return ["(empty file)"]

    if center_line is not None and 1 <= center_line <= total:
        start = max(1, center_line - radius)
        end = min(total, center_line + radius)
    else:
        start = 1
        end = min(total, max_lines)

    rows = []
    for idx in range(start, end + 1):
        rows.append("{:>4} | {}".format(idx, content[idx - 1]))
    if end < total:
        rows.append("  ... | ({} more lines)".format(total - end))
    return rows


def find_line_number(path: Path, needle: str) -> Optional[int]:
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return i
    return None


def print_change_preview(changed: List[Path], scenario_key: str) -> None:
    root = repo_root()
    print("changePreview:")

    has_preview = False
    for path in changed:
        if not path.exists() or not path.is_file():
            continue

        rel = path.relative_to(root)
        center = None

        if path.name == "main.jsx":
            center = find_line_number(path, IMPORT_MARKER)
        elif path.name == "package.json":
            if scenario_key == "unused-dependencies":
                center = find_line_number(path, '"left-pad"')
            elif scenario_key == "unlisted-binaries":
                center = find_line_number(path, '"knip:scenario:unlisted-binary"')

        print("- file: {}".format(rel))
        for row in line_preview(path, center_line=center):
            print("  {}".format(row))
        has_preview = True

    if not has_preview:
        print("- (no file preview)")


def run_verify(scenario: Dict[str, object], target_root: Path) -> int:
    include_type = str(scenario["include_type"])
    expected_issue = str(scenario["expected_issue"])

    cmd = ["npm", "run", "knip", "--", "--reporter", "json", "--include", include_type, "--no-exit-code"]
    proc = subprocess.run(cmd, cwd=repo_root(), capture_output=True, text=True)
    if proc.stderr.strip():
        print(proc.stderr.strip())

    data = extract_json(proc.stdout)
    if not data:
        print("[error] Failed to parse Knip JSON output.")
        print(proc.stdout.strip())
        return 1

    count, matches = summarize_matches(data, scenario, target_root)

    print("verifySummary:")
    print("- expectedIssue: {}".format(expected_issue))
    print("- includeType: {}".format(include_type))
    print("- detectedCount: {}".format(count))
    print("- matches:")
    if matches:
        for item in matches[:20]:
            print("  - {}".format(item))
        if len(matches) > 20:
            print("  - ... and {} more".format(len(matches) - 20))
    else:
        print("  - (none)")

    if count > 0:
        print("[ok] Expected issue detected")
        return 0

    if SCENARIO_KEY == "duplicate-exports":
        print("[warn] No duplicates detected in current Knip version/output. This scenario may fall back to other issue types.")
        return 0

    print("[error] Expected issue not detected")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="{} scenario controller".format(SKILL_NAME))
    parser.add_argument("--mode", choices=["create", "cleanup", "verify"], required=True)
    parser.add_argument("--targetRoot", default=None)
    args = parser.parse_args()

    scenario = SCENARIOS[SCENARIO_KEY]
    target_root = resolve_target_root(args.targetRoot, str(scenario["target_subdir"]))

    print("skill: {}".format(SKILL_NAME))
    print("mode: {}".format(args.mode))
    print("targetRoot: {}".format(target_root))
    print("expectedIssue: {}".format(scenario["expected_issue"]))
    print("verifyCommand: npm run knip -- --reporter json --include {} --no-exit-code".format(scenario["include_type"]))

    changed: List[Path] = []

    if args.mode == "create":
        apply_scenario_create(SCENARIO_KEY, target_root, changed)
    elif args.mode == "cleanup":
        apply_scenario_cleanup(SCENARIO_KEY, target_root, changed)
    else:
        return run_verify(scenario, target_root)

    print("changedFiles:")
    if changed:
        for p in changed:
            print("- {}".format(p))
    else:
        print("- (none)")

    if args.mode == "create":
        print_change_preview(changed, SCENARIO_KEY)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
