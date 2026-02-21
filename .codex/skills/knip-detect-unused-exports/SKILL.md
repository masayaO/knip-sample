---
name: knip-detect-unused-exports
description: Knipの「unused exports」を意図的に再現したい時に使う。検証コードを create/verify/cleanup の3モードで安全に操作し、検証後は cleanup で元に戻す時に使う。
---

# Knip Detect Unused Exports

## Quick Flow

1. 検証コードを生成する。

```bash
python3 .codex/skills/knip-detect-unused-exports/scripts/scenario.py --mode create
```

2. Knipで検出を確認する。

```bash
python3 .codex/skills/knip-detect-unused-exports/scripts/scenario.py --mode verify
```

3. 検証後は必ず元に戻す。

```bash
python3 .codex/skills/knip-detect-unused-exports/scripts/scenario.py --mode cleanup
```

## Scenario

- 目的: 未使用エクスポート (`unused exports`) を再現する
- create動作: 未参照export関数を含むファイルを作成する。
- cleanup動作: 検証用ディレクトリを削除する。

## Safety Rules

- 変更対象は原則 `src/knip-lab/<issue>/` または `package.json` の最小差分に限定する。
- 1つのシナリオを適用中に、他のシナリオを重ねて実行しない。
- cleanup後に `git status` で差分が残っていないことを確認する。

## Expected Output

- `verify` 実行時に Knip の出力で `unused exports` に対応する問題が1件以上確認できる。
- スクリプトは `changedFiles`、`expectedIssue`、`verifyCommand` を出力する。

## Rollback Rules

- cleanupに失敗した場合は同じコマンドを再実行する。
- `package.json` を変更するシナリオでは、必要に応じて `npm install --package-lock-only --ignore-scripts` を実行して lockfile を再同期する。

## Reporting Rules

- 出力は「生ログ貼り付け」ではなく、ユーザー向けに短い進行メッセージで説明する。
- 冒頭で1-2文: 「今から何のKnip挙動を試すか」を自然文で伝える。
- `create` 後に1-3文: 「何を追加/変更したか」を伝え、`changePreview` から最小1つのコード断片（行番号付き）だけ提示する。
- `verify` 前に1文: 「今からKnipで検出確認する」と伝える。
- `verify` 後に1-2文: 「何が何件検出されたか」を `verifySummary.detectedCount` と `matches` で要約して伝える。
- `cleanup` 前後で各1文: 「片付ける」→「片付け完了」を伝える。
- 最後に締め1-2文: 「今回のシミュレーションで、どの変更をKnipで検知できたか」を自然文でまとめる。
- `simulationIntro` / `runSummary` / `changePreview` / `verifySummary` は、必要箇所だけ読み取って要約し、全文をそのまま貼らない。
- 実行は最終一括報告ではなく、`create` / `verify` / `cleanup` の各ステップ完了直後に都度ユーザーへ1-3文で報告する。
- ステップ報告の基本形: 「今から何をする」→「実行した」→「結果（件数/対象）」→「次に何をする」。
