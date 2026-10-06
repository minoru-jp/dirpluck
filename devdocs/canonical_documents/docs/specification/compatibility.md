<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/compatibility.py` です。
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

# Pre-1.0 compatibility

この文書の規則は現在の 0.x series の互換入力・互換挙動だけを定義する。Canonical input の意味論ではなく、明記した replacement への移行期間を提供するための仕様であり、1.0.0 ではすべて削除する。

## SECTION_1301

title: Deprecated Selection references

### SPEC_068

0.14.0 から 1.0.0 未満では、従来の1要素 nested array Shared reference (`["name"]`) と、`ignore` で `./` から始まる1要素 nested array path reference (`["./path"]`) を互換入力として受理するが、これらは非推奨とする。新規 Configuration は `{ shared = "..." }` / `{ path = "..." }` を使用する。CLI は実行時に読み込んだ各 Configuration file について、有効な deprecated nested-array reference が1個以上あればその file につき1回だけ stderr へ warning を表示し、1.0.0 で削除されることと replacement syntax を案内する。公式 Python API の `dirpluck.run()` は、読み込んだ各 Configuration file について同じ診断を Python の warnings framework に公開 `ConfigurationDeprecationWarning` (`FutureWarning` subclass) として1回報告し、`RunResult.warnings` には含めない。この warning は Python の既定 filter で表示対象とし、warning location は固定 `stacklevel` ではなく dirpluck package 外の最初の caller frame に帰属させる。Base chain の Configuration も読み込まれた Configuration として同じ扱いにする。CLI は同じ診断を stderr 表示用に収集するため、追加の `ConfigurationDeprecationWarning` は発行しない。これらの warning は CLI の stdout と exit status を変更しない。1.0.0 では deprecated nested-array reference を Configuration syntax から削除し、invalid Configuration とする。Nested array は互換期間中も要素数ちょうど1の non-empty string だけを互換入力として認め、`[]`、`["foo", "bar"]`、`[123]` は error とする。

level: MUST

## SECTION_1302

title: Legacy Pluck Case syntax

### SPEC_170

0.16.0 から 1.0.0 未満では legacy `[pluck.case.<name>]` を canonical `[case.pluck.<name>]` と同じ Pluck Case definition として互換受理し、Base composition / runtime Case semantics も canonical form と同一とする。`ConfigurationDeprecationWarning` で `[case.pluck.<name>]` への移行を案内する。同じ Configuration document に同名 Case が legacy / canonical の両方で定義された場合は precedence を設けず error とする。1.0.0 では legacy syntax を削除する。Always Case は legacy alias を持たず `[case.always.<name>]` だけを受理する。

level: MUST

## SECTION_1303

title: Always Namespace compatibility

### SPEC_064

0.16.0 以上 1.0.0 未満では Always source の optional `namespace` field を pre-1.0 compatibility として受理し、effective `[namespace.<name>]` を参照する。Scope の prefix semantics は使用せず、Namespace name が `[always.<name>]` の `<name>` を置き換えた effective Always name として final archive root に使用される。Source filesystem path と Selection boundary は変更しない。Unknown ネームスペース reference は Configuration error とし、override 後の final archive root は通常の Archive identity / collision rule に従う。Canonical replacement は、必要な Archive directory name を `[always.<name>]` の `<name>` に直接記述することである。1.0.0 では Always source schema から `namespace` field を削除し、指定した Configuration を invalid とする。

level: MUST

### SPEC_167

0.16.0 から 1.0.0 未満で Always `namespace` を使用した Configuration は `AlwaysMigrationWarning` を報告し、この field が 1.0.0 で削除されることと、Archive directory name を `[always.<name>]` に直接記述する replacement を案内する。この warning は layout migration warning の有無とは独立して報告する。1.0.0 では Always `namespace` の受理とこの migration warning をともに削除する。

level: MUST

## SECTION_1304

title: Always archive layout migration warning

### SPEC_171

0.16.0 から 1.0.0 未満では、effective Layout を持たない Always source について 0.14.x で有効だった Archive identity と 0.16.x の effective Always name を比較し、両者が異なる場合だけ `AlwaysMigrationWarning` を報告する。Warning は旧 root と 0.16.x root を含める。0.17.0 以降で effective Layout が有効な Always source では、この legacy layout migration warning を報告してはならない。Explicit Layout が現在の final Archive destination を決めており、0.16.x の中間 placement は current output を表さないためである。Always `namespace` の削除 warning はこの抑制とは独立する。

level: MUST
