## Skills
このリポジトリで使うCodex Skillを定義します。必要なときは以下を優先して使用してください。

### Available skills
- knip-detect-unused-files: `unused files` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unused-files/SKILL.md)
- knip-detect-unused-dependencies: `unused devDependencies` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unused-dependencies/SKILL.md)
- knip-detect-unused-exports: `unused exports` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unused-exports/SKILL.md)
- knip-detect-unlisted-dependencies: `unlisted dependencies` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unlisted-dependencies/SKILL.md)
- knip-detect-unlisted-binaries: `unlisted binaries` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unlisted-binaries/SKILL.md)
- knip-detect-unresolved-imports: `unresolved imports` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unresolved-imports/SKILL.md)
- knip-detect-duplicate-exports: `duplicate exports` の再現を試す検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-duplicate-exports/SKILL.md)
- knip-detect-unused-exported-types: `unused exported types` を意図的に発生させる検証スキル。 (file: /Users/masayaokuda/workspace/github.com/masayaO/knip-sample/.codex/skills/knip-detect-unused-exported-types/SKILL.md)

### How to use skills
- Trigger rules: ユーザーがスキル名（`$knip-detect-*` または平文）を指定した場合、またはタスク内容がスキル説明に一致する場合はそのスキルを使う。
- Discovery: 実装前に必要箇所だけ `SKILL.md` を開き、手順に従う。
- Minimal loading: 参照先ファイルは必要なものだけ開く。不要な一括読み込みはしない。
- Multiple skills: 複数候補がある場合は最小セットを選び、適用順を短く明示する。
- Fallback: スキル適用が難しい場合は理由を短く示し、通常手順で継続する。
