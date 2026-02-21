# Knipでできること

Knipは、JavaScript/TypeScriptプロジェクトの「使われていないもの」や「宣言漏れ」を静的解析で検出するツールです。  
このドキュメントでは、主要な検出項目と、このリポジトリでの最小実行方法をまとめます。

## 1. 未使用ファイル (Unused Files)

どのエントリーポイントからも到達できないファイルを検出します。  
補足: 到達可能性の判定は `entry` / `project` の設定に依存するため、設定範囲外のファイルは検出対象から外れる場合があります。

## 2. 未使用依存関係 (Unused Dependencies)

`package.json` に記載されている依存パッケージのうち、コードや設定ファイルから参照されていないものを検出します。  
補足: プラグインや設定経由でのみ使う依存は、設定によっては未使用に見えることがあるため、結果を確認してから削除してください。

## 3. 未使用エクスポート (Unused Exports)

`export` されているが、他のファイルから参照されていない関数・変数・型などを検出します。  
補足: ライブラリ公開APIのように外部利用前提のエクスポートは、プロジェクト内参照がなくても意図的な場合があります。

## 4. 未登録依存関係 (Unlisted Dependencies)

コード内で `import` / `require` しているのに、`package.json` に宣言されていない依存を検出します。  
補足: 実行時に解決される想定でも、宣言漏れのままだと再現性やCI安定性を損なうため、明示的な登録が推奨です。

## その他に検出できる主な項目

- `Unlisted binaries`: 実行しているCLIが依存として宣言されていない
- `Unresolved imports`: import先を解決できない
- `Duplicate exports`: 重複したエクスポート
- `Unused exported types`: 参照されないエクスポート型

## このリポジトリでの実行方法

このリポジトリでは `package.json` に `knip` スクリプトを設定済みです。

```bash
npm run knip
```

必要に応じて自動修正モードも利用できます。

```bash
npx knip --fix
```

注意:

- `--fix` は一部の項目を自動修正できますが、変更内容は必ずレビューしてください。
- 特に依存削除やエクスポート変更は、実行時や外部利用への影響確認を推奨します。

## 参考リンク（公式）

- https://knip.dev/reference/issue-types
- https://knip.dev/features/auto-fix
- https://knip.dev/guides/handling-issues
- https://knip.dev/guides/configuring-project-files
