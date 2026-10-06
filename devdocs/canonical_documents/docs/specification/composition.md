<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/composition.py` です。
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

# Base chain and composition

## SPEC_025

基底設定ファイルは `[about].base` として宣言する。`base` は concrete Configuration file path とし、空文字列と glob を拒否する。Relative path は Filesystem path notation の共通規則に従って現在の Configuration file directory から解決し、absolute path は host filesystem 上の file を直接参照する。Path は `.dirpluck` extension を必要とし、host OS の通常の filesystem semantics に従って参照する。解決先は実在 regular file で、内容が有効な TOML Configuration schema でなければならない。

level: MUST

related: [SPEC_003](document-selection.md#spec_003), [SPEC_018](paths.md#spec_018)

## SPEC_026

各 Configuration が参照できる base は0個または1個とする。Base Configuration がさらに `base` を持つ場合は linear chain を形成する。Depth に固定上限は設けない。

level: MUST

## SECTION_401

title: Cycle detection

### SPEC_027

Base chain が同じ Configuration file へ戻る参照を含む場合は cycle error とする。Symbolic link / Windows junction など異なる document path alias を経由して同じ実体 Configuration file へ戻る場合も cycle とみなす。

level: MUST

condition: base chain の cycle を判定する場合

## SECTION_402

title: Definition composition

### SPEC_029

`[about].description` / `description_no_targets` / `description_no_always` / `description_empty` / `always_layout` / `targets_layout` は field ごとに Root Configuration から Base chain をたどり、最初に定義された値を effective value とする。Chain 全体に定義がなければその effective value は存在しない。`about.base` は chain link であり継承対象の値ではない。Base Configuration に書かれた `[scope]` はその Configuration 自身を Root として使う場合の default Scope 設定であり、outer Root の default Scope へ継承しない。

level: MUST

### SPEC_030

- Pluck default Selection: Base chain 上で同じ default Selection が複数定義される場合は Root に近い Configuration の `[pluck]` が優先する。Case definition だけを持つ Configuration は Base 側の default Selection を隠さない。
- Pluck Case: `[case.pluck.<name>]` は Case name ごとに統合し、同名 Case は Root に近い Configuration の complete Selection definition 全体を採用し、異なる名前はすべて残す。
- Always source: 同名 source は Root に近い Configuration の definition 全体を採用し、異なる名前はすべて残す。
- Always Case: `[case.always.<name>]` は Case name ごとに統合し、同名 Case は Root に近い Configuration の `description` / `include` / `exclude` を含む definition 全体を採用し、異なる名前はすべて残す。
- Named Scope: 同名 Scope は Root に近い Configuration の `description` / `target_kind` / `path` / `ignore` / `layout` / `namespace` を含む definition 全体を採用し、異なる名前はすべて残す。Default Scope は Base から継承せず、Runtime Target, Scope, and Case の default Scope rule に従って Root Configuration location から root を決め、Root Configuration の `[scope]` に書かれた `description` / `target_kind` / `ignore` / `layout` / `namespace` だけを使う。
- Layout: 同名 Layout は Root に近い Configuration の definition 全体を採用し、異なる名前はすべて残す。Composition 後の effective Layout name は大文字小文字を区別しない比較で一意でなければならない。`[about].always_layout` / `[about].targets_layout` と source 個別 `layout` reference は Base composition 後の effective Layout 集合に対して解決する。
- ネームスペース: 同名 Namespace は Root に近い Configuration の definition 全体を採用し、異なる名前はすべて残す。Scope の Namespace reference は Base composition 後の effective Namespace 集合に対して解決する。
- Shared pattern: `must` / `may` / `ignore` を独立した namespace とし、各 namespace の同名 pattern set は Root に近い Configuration の配列全体を採用する。

level: MUST

### SPEC_034

Selection の Shared reference は Base composition 後の effective shared namespace に対して解決する。Root に近い Configuration は、Base 側の source definition が参照する同名 pattern set を追加または置き換えられる。

level: MUST

## SECTION_403

title: Output と base chain

### SPEC_035

Configuration は Output を省略でき、共通 definition だけを提供する Base Configuration として利用できる。Base Configuration の Output は Root Configuration へ継承しない。Archive planning と `--preview` は Root Output を必要としない。実際に Archive file を書き込む build ではルート設定ファイル自身が直接宣言した Output だけを使用し、Root が Output を持たない場合は build error とする。

level: MUST

condition: Archive file を書き込む build
