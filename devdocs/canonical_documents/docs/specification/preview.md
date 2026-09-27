<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/preview.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/canonical_documents/` にある日本語 canonical document はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの canonical document を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や canonical document を直接編集するのではなく、正本へ戻って行う。
-->

# Preview

## SPEC_145

`--preview` は通常実行と同じ base chain resolution、cycle detection、definition composition、Scope lookup / expansion、Target direct-child resolution と Scope ignore filtering、Case selection、file selection、archive planning を使うが、output file / directory を作成・変更しない。Root Configuration に Output declaration がなくても使用できる。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--archive-mtime` は preview でも validation するが、Archive を書かないため preview result には影響しない。

level: MUST

condition: `--preview` を使用する場合

related: [SPEC_028](composition.md#spec_028), [SPEC_037](runtime-targets.md#spec_037), [SPEC_065](selection.md#spec_065), [SPEC_098](archive.md#spec_098), [SPEC_107](output.md#spec_107)

## SPEC_146

不足する `must` pattern は `[missing]`、不足する `may` pattern は `[optional missing]` と表示する。最終 selection 0件は policy に応じて `empty, allowed` または `empty, would error` と表示する。

level: MUST

condition: `--preview` で selection result を表示する場合

## SPEC_147

不正 base path、base cycle、duplicate effective Scope root、使用した Scope root の不在、unknown Scope、不正 Target reference、direct-child boundary を外れる Target、未解決 Shared / Namespace reference、不正 source path、Case inconsistency、duplicate final archive root、Output schema / base-chain write-boundary conflict など Configuration と planning の error は preview でも error とする。未使用の named Scope root が現在存在しないことだけでは error にしない。Base depth 自体は error / warning にしない。

level: MUST

condition: `--preview` で configuration / planning error を検出した場合
