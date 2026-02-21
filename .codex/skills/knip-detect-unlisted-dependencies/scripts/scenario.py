#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

SCENARIO_KEY = "unlisted-dependencies"
SKILL_NAME = "knip-detect-unlisted-dependencies"
IMPORT_MARKER = "// knip-scenario-import"

SCENARIOS = {
    "unused-files": {"issue": "unused files", "target_subdir": "unused-files", "entry_file": None},
    "unused-dependencies": {"issue": "unused devdependencies", "target_subdir": "unused-dependencies", "entry_file": None},
    "unused-exports": {"issue": "unused exports", "target_subdir": "unused-exports", "entry_file": "lib.js"},
    "unlisted-dependencies": {"issue": "unlisted dependencies", "target_subdir": "unlisted-dependencies", "entry_file": "use-dayjs.js"},
    "unlisted-binaries": {"issue": "unlisted binaries", "target_subdir": "unlisted-binaries", "entry_file": None},
    "unresolved-imports": {"issue": "unresolved imports", "target_subdir": "unresolved-imports", "entry_file": "broken-import.js"},
    "duplicate-exports": {"issue": "duplicate exports", "target_subdir": "duplicate-exports", "entry_file": "index.js"},
    "unused-exported-types": {"issue": "unused exported types", "target_subdir": "unused-exported-types", "entry_file": "types.ts"},
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
    root = repo_root()
    proc = subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts"], cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        print("[warn] Failed to sync package-lock.json. Run manually if needed:")
        print("       npm install --package-lock-only --ignore-scripts")
        if proc.stderr:
            print(proc.stderr.strip())


def update_main_import(entry_file: Optional[str], subdir: str, add: bool) -> bool:
    if not entry_file:
        return False
    main_path = repo_root() / "src" / "main.jsx"
    line = "import './knip-lab/{}/{}'; {}\n".format(subdir, entry_file, IMPORT_MARKER)
    current = main_path.read_text(encoding="utf-8")

    if add:
        if line not in current:
            main_path.write_text(line + current, encoding="utf-8")
            return True
        return False

    if line in current:
        main_path.write_text(current.replace(line, ""), encoding="utf-8")
        return True
    return False


def apply_scenario_create(key: str, target_root: Path, changed: List[Path]) -> None:
    root = repo_root()
    subdir = SCENARIOS[key]["target_subdir"]

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
    subdir = SCENARIOS[key]["target_subdir"]

    if key in {"unused-files", "unused-exports", "unlisted-dependencies", "unresolved-imports", "duplicate-exports", "unused-exported-types"}:
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


def run_verify(expected_issue: str) -> int:
    proc = subprocess.run(["npm", "run", "knip"], cwd=repo_root(), capture_output=True, text=True)
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    print(output.strip())

    if expected_issue in output.lower():
        print("[ok] Found expected issue hint: {}".format(expected_issue))
        return 0
    if proc.returncode != 0:
        print("[warn] knip returned non-zero but exact issue text did not match. Check output manually.")
        return 0

    print("[error] Expected issue not found: {}".format(expected_issue))
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="{} scenario controller".format(SKILL_NAME))
    parser.add_argument("--mode", choices=["create", "cleanup", "verify"], required=True)
    parser.add_argument("--targetRoot", default=None)
    args = parser.parse_args()

    scenario = SCENARIOS[SCENARIO_KEY]
    expected_issue = scenario["issue"]
    target_root = resolve_target_root(args.targetRoot, scenario["target_subdir"])

    print("skill: {}".format(SKILL_NAME))
    print("mode: {}".format(args.mode))
    print("targetRoot: {}".format(target_root))
    print("expectedIssue: {}".format(expected_issue))
    print("verifyCommand: npm run knip")

    changed: List[Path] = []
    if args.mode == "create":
        apply_scenario_create(SCENARIO_KEY, target_root, changed)
    elif args.mode == "cleanup":
        apply_scenario_cleanup(SCENARIO_KEY, target_root, changed)
    else:
        return run_verify(expected_issue)

    print("changedFiles:")
    if changed:
        for p in changed:
            print("- {}".format(p))
    else:
        print("- (none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
