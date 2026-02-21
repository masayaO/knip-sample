---
name: knip-detect-unused-dependencies
description: Knipの「unused dependencies」を意図的に再現したい時に使う。検証コードを create/verify/cleanup の3モードで安全に操作し、検証後は cleanup で元に戻す時に使う。
---

# Knip Detect Unused Dependencies

## Quick Flow

1. 検証コードを生成する。

```bash
python3 .codex/skills/knip-detect-unused-dependencies/scripts/scenario.py --mode create
```

2. Knipで検出を確認する。

```bash
python3 .codex/skills/knip-detect-unused-dependencies/scripts/scenario.py --mode verify
```

3. 検証後は必ず元に戻す。

```bash
python3 .codex/skills/knip-detect-unused-dependencies/scripts/scenario.py --mode cleanup
```

## Scenario

- 目的: 未使用依存関係 (`unused dependencies`) を再現する
- create動作: package.json の devDependencies に left-pad を追加する。
- cleanup動作: left-pad を devDependencies から削除し、lockfile 再同期を試みる。

## Safety Rules

- 変更対象は原則 `src/knip-lab/<issue>/` または `package.json` の最小差分に限定する。
- 1つのシナリオを適用中に、他のシナリオを重ねて実行しない。
- cleanup後に `git status` で差分が残っていないことを確認する。

## Expected Output

- `verify` 実行時に Knip の出力で `unused dependencies` に対応する問題が1件以上確認できる。
- スクリプトは `changedFiles`、`expectedIssue`、`verifyCommand` を出力する。

## Rollback Rules

- cleanupに失敗した場合は同じコマンドを再実行する。
- `package.json` を変更するシナリオでは、必要に応じて `npm install --package-lock-only --ignore-scripts` を実行して lockfile を再同期する。

## Reporting Rules

- `create` 実行後は、標準出力の `changePreview` を要約せずにそのまま表示する。
- 少なくとも1ファイル分は、行番号付きコード断片をそのまま示す。
- `verify` 実行後は `verifySummary.detectedCount` と `matches` を必ず表示する。
- 各モードの開始時に出る `simulationIntro` を、要約せずそのまま表示する。
- 各モードの終了時に出る `runSummary` を、要約せずそのまま表示する。
