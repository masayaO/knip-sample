#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

SCENARIO_KEY = "unused-exported-types"
SKILL_NAME = "knip-detect-unused-exported-types"
IMPORT_MARKER = "// knip-scenario-import"

SCENARIOS: Dict[str, Dict[str, object]] = {
    "unused-files": {
        "expected_issue": "unused files",
        "include_type": "files",
        "target_subdir": "unused-files",
        "entry_file": None,
        "simulation": "どこからも参照されない孤立ファイルを作り、Knipが未使用ファイルを検出できる挙動を試す。",
    },
    "unused-dependencies": {
        "expected_issue": "unused devdependencies",
        "include_type": "dependencies",
        "target_subdir": "unused-dependencies",
        "entry_file": None,
        "simulation": "package.jsonに未使用のdevDependencyを追加し、Knipが未使用依存を検出できる挙動を試す。",
    },
    "unused-exports": {
        "expected_issue": "unused exports",
        "include_type": "exports",
        "target_subdir": "unused-exports",
        "entry_file": "lib.js",
        "simulation": "未参照のexport関数を作り、Knipが未使用エクスポートを検出できる挙動を試す。",
    },
    "unlisted-dependencies": {
        "expected_issue": "unlisted dependencies",
        "include_type": "unlisted",
        "target_subdir": "unlisted-dependencies",
        "entry_file": "use-dayjs.js",
        "simulation": "未宣言パッケージをimportして、Knipが未登録依存を検出できる挙動を試す。",
    },
    "unlisted-binaries": {
        "expected_issue": "unlisted binaries",
        "include_type": "binaries",
        "target_subdir": "unlisted-binaries",
        "entry_file": None,
        "simulation": "未宣言CLIをscriptsで呼び出し、Knipが未登録バイナリを検出できる挙動を試す。",
    },
    "unresolved-imports": {
        "expected_issue": "unresolved imports",
        "include_type": "unresolved",
        "target_subdir": "unresolved-imports",
        "entry_file": "broken-import.js",
        "simulation": "存在しないモジュールをimportして、Knipが未解決importを検出できる挙動を試す。",
    },
    "duplicate-exports": {
        "expected_issue": "duplicate exports",
        "include_type": "duplicates",
        "target_subdir": "duplicate-exports",
        "entry_file": "index.js",
        "simulation": "重複したexport定義を作り、Knipが重複エクスポートを検出できる挙動を試す。",
    },
    "unused-exported-types": {
        "expected_issue": "unused exported types",
        "include_type": "types",
        "target_subdir": "unused-exported-types",
        "entry_file": "types.ts",
        "simulation": "未参照のexport typeを作り、Knipが未使用エクスポート型を検出できる挙動を試す。",
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


def display_path(path: Path) -> str:
    root = repo_root()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_lockfile(changed: List[Path]) -> None:
    lockfile = repo_root() / "package-lock.json"
    before = lockfile.read_text(encoding="utf-8") if lockfile.exists() else None

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
        return

    after = lockfile.read_text(encoding="utf-8") if lockfile.exists() else None
    if before != after:
        changed.append(lockfile)


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
            sync_lockfile(changed)
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
    print("changePreview:")

    has_preview = False
    for path in changed:
        if not path.exists() or not path.is_file():
            continue

        center = None

        if path.name == "main.jsx":
            center = find_line_number(path, IMPORT_MARKER)
        elif path.name == "package.json":
            if scenario_key == "unused-dependencies":
                center = find_line_number(path, '"left-pad"')
            elif scenario_key == "unlisted-binaries":
                center = find_line_number(path, '"knip:scenario:unlisted-binary"')

        print("- file: {}".format(display_path(path)))
        for row in line_preview(path, center_line=center):
            print("  {}".format(row))
        has_preview = True

    if not has_preview:
        print("- (no file preview)")


def build_verify_command(scenario: Dict[str, object]) -> str:
    _ = scenario
    return "npm run knip"


def build_cleanup_commands(changed: List[Path], target_root: Path) -> List[str]:
    root = repo_root()
    restore_files: List[str] = []

    for path in changed:
        if not path.is_absolute():
            continue
        if not str(path).startswith(str(root)):
            continue
        rel = path.relative_to(root)
        if rel == Path("package.json") or rel == Path("package-lock.json") or rel == Path("src/main.jsx"):
            restore_files.append(str(rel))

    dedup_restore = list(dict.fromkeys(restore_files))

    commands: List[str] = []
    if dedup_restore:
        commands.append("git restore -- {}".format(" ".join(dedup_restore)))

    commands.append("rm -rf {}".format(target_root))
    return commands


def print_intro(mode: str, scenario: Dict[str, object], target_root: Path) -> None:
    print("simulationIntro:")
    print("- skill: {}".format(SKILL_NAME))
    print("- mode: {}".format(mode))
    print("- whatToSimulate: {}".format(scenario["simulation"]))
    print("- expectedIssue: {}".format(scenario["expected_issue"]))
    print("- targetRoot: {}".format(target_root))
    print("- verifyWith: {}".format(build_verify_command(scenario)))


def print_outro(mode: str, scenario: Dict[str, object], changed: List[Path], status: str = "ok") -> None:
    print("runSummary:")
    print("- mode: {}".format(mode))
    print("- simulatedIssue: {}".format(scenario["expected_issue"]))
    print("- status: {}".format(status))
    print("- changedCount: {}".format(len(changed)))
    print("- changedFiles:")
    if changed:
        for p in changed:
            print("  - {}".format(display_path(p)))
    else:
        print("  - (none)")


def print_next_steps(scenario: Dict[str, object], changed: List[Path], target_root: Path) -> None:
    print("nextSteps:")
    print("- verifyCommand: {}".format(build_verify_command(scenario)))
    print("- cleanupCommands:")
    for command in build_cleanup_commands(changed, target_root):
        print("  - {}".format(command))


def main() -> int:
    parser = argparse.ArgumentParser(description="{} scenario controller".format(SKILL_NAME))
    parser.add_argument("--mode", choices=["create"], required=True)
    parser.add_argument("--targetRoot", default=None)
    args = parser.parse_args()

    scenario = SCENARIOS[SCENARIO_KEY]
    target_root = resolve_target_root(args.targetRoot, str(scenario["target_subdir"]))

    print_intro(args.mode, scenario, target_root)

    changed: List[Path] = []
    apply_scenario_create(SCENARIO_KEY, target_root, changed)

    print("changedFiles:")
    if changed:
        for p in changed:
            print("- {}".format(p))
    else:
        print("- (none)")

    print_change_preview(changed, SCENARIO_KEY)
    print_outro(args.mode, scenario, changed, status="ok")
    print_next_steps(scenario, changed, target_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
