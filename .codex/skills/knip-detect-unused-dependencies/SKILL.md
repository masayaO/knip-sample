---
name: knip-detect-unused-dependencies
description: Knipの「unused devDependencies」を意図的に再現したい時に使う。検証用の差分を create で生成し、Knip実行とcleanupは手動で行う create-only スキル。
---

# Knip Detect Unused Dependencies

## Quick Flow

1. 検証コードを生成する。

```bash
python3 .codex/skills/knip-detect-unused-dependencies/scripts/scenario.py --mode create
```

2. `npm run knip` を実行して手動検証する。
   （`nextSteps.verifyCommand` は `npm run knip` を返す）
3. 出力された `nextSteps.cleanupCommands` で手動cleanupする。

## Scenario

- 目的: `unused devDependencies` を再現する
- create動作: package.json の devDependencies に left-pad を追加する。

## Safety Rules

- 変更対象は原則 `src/knip-lab/<issue>/` または `package.json` の最小差分に限定する。
- 1つのシナリオを適用中に、他のシナリオを重ねて実行しない。
- このスキルはリポジトリ状態を自動で元に戻さない。検証後は必ず `nextSteps.cleanupCommands` を手動実行する。

## Expected Output

- スクリプトは `simulationIntro`、`changedFiles`、`changePreview`、`runSummary`、`nextSteps` を出力する。
- `nextSteps.verifyCommand` には `npm run knip` が表示される。
- `nextSteps.cleanupCommands` に手動復旧用のコマンド群が表示される。

## Manual Verify/Cleanup

- verify: `npm run knip` を実行して Knip の検出結果を確認する。
- 参考: `nextSteps.verifyCommand` にも同じコマンド（`npm run knip`）が表示される。
- cleanup: `nextSteps.cleanupCommands` を上から順に実行して差分を元に戻す。
- 必要に応じて `git status` で差分が解消されたことを確認する。

## Reporting Rules

- 出力は「生ログ貼り付け」ではなく、ユーザー向けに短い進行メッセージで説明する。
- 冒頭で1-2文: 「今から何のKnip挙動を試すか」を自然文で伝える。
- `create` 後に1-3文: 「何を追加/変更したか」を伝え、`changePreview` から最小1つのコード断片（行番号付き）だけ提示する。
- このスキルでは `verify` と `cleanup` を自動実行しない。`nextSteps` のコマンドを提示して手動実行を案内する。
- 最後に締め1-2文: 「今回のシミュレーションで、次に何を手動実行すればよいか」を自然文でまとめる。
- `simulationIntro` / `runSummary` / `changePreview` / `nextSteps` は、必要箇所だけ読み取って要約し、全文をそのまま貼らない。
