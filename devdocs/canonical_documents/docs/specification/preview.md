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

`--preview` は、同じ Configuration / Target / Case / Selection 入力から通常 build が作成する Archive plan と同じ source selection と Archive 内配置を表示し、output file / directory を作成・変更しない。Root Configuration に Output declaration がなくても使用できる。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--archive-mtime` は preview でも validation するが、Archive を書かないため preview result には影響しない。

level: MUST

condition: `--preview` を使用する場合

related: [SPEC_098](archive.md#spec_098), [SPEC_107](output.md#spec_107)

## SPEC_146

Preview は不足する required `must` と optional `may` を区別し、path ではない Selection expression を filesystem path と誤解させない形で未一致として表現する。最終 selection が0件の場合は、現在の `allow_empty` policy で成功可能か通常 build なら error になるかを判別できるようにする。型 marker の不一致候補が検出された `must` / `may` は selection result の required / optional missing semantics を変えず、source を識別できる non-fatal diagnostic も生成する。CLI `--preview` はその diagnostic を stderr へ報告し、Python API の `preview=True` は `RunResult.warnings` に返す。Tree node の exact label、記号、整形は互換性契約に含めない。

level: MUST

condition: `--preview` で selection result を表示する場合

## SPEC_147

`--preview` でも、有効な Archive plan を構築するために必要な Configuration / Base / Scope / Target / Shared / Namespace / Case / Selection / Archive layout の validation を省略しない。使用した Scope root や source path が解決できない場合は error とする一方、未使用の named Scope root が現在存在しないことだけでは error にしない。Archive を実際に書き込む処理だけに必要な destination existence / replacement validation は preview の契約に含めない。

level: MUST

condition: `--preview` で Archive plan を構築する場合
