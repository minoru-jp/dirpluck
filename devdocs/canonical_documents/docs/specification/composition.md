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

Base resolution では、診断と relative path resolution のために各 Configuration の選択された document location を保持しつつ、cycle identity は symbolic link / junction alias を解決した実体 file path で比較する。alias 解決後に同じ physical Configuration path となる Configuration が別の document path alias から現在の chain に再登場した場合も cycle error とし、診断には選択された document location の chain を含める。Depth 自体による error / warning は行わない。

level: MUST

condition: base chain の cycle identity を判定する場合

## SECTION_402

title: Definition composition

### SPEC_028

Chain の最深部を初期値とし、1 layer ずつ外側の definition を重ねて実効設定を構成する。

level: MUST

### SPEC_029

`[about].description` は outermost layer から inner layer へ探索し、最初に定義された値を effective description とする。Chain 全体に定義がなければ effective description は存在しない。`about.base` は chain link であり effective value として shadow / merge しない。Base layer に書かれた `[scope]` はその Configuration 自身を Root として使う場合の default Scope 設定であり、outer Root の default Scope へ継承しない。

level: MUST

### SPEC_030

- Pluck: outer layer に Pluck があれば inner Pluck definition 全体を shadow する。
- Always source: 同名 source は outer layer が definition 全体を shadow し、異なる名前は保持する。
- Named Scope: 同名 Scope は outer layer が `description` / `target_kind` / `path` / `ignore` / `namespace` を含む definition 全体を shadow し、異なる名前は保持する。Default Scope は compose せず、Runtime Target, Scope, and Case の default Scope rule に従って Root Configuration location から root を決め、root Configuration の `[scope]` に書かれた `description` / `target_kind` / `ignore` / `namespace` だけを使う。
- ネームスペース: 同名 Namespace は outer layer が definition 全体を shadow し、異なる名前は保持する。Scope / Always の Namespace reference は composition 後の effective Namespace 集合に対して解決する。
- Shared pattern: `must` / `may` / `ignore` を独立した namespace とし、各 namespace の同名 pattern set は outer layer が配列全体を shadow する。

level: MUST

### SPEC_031

Pluck / Always / named Scope / ネームスペース の shadow は field 単位の partial merge ではない。Source definition の Case も source definition と一緒に置き換える。

level: MUST NOT

### SPEC_032

Named Scope root と Always source path は、その definition を記述した Configuration file の directory を基準として解決する。Base から残った definition は origin の resolution result を保持し、outer layer へ rebase しない。Default Scope は path field を持たず、Runtime Target, Scope, and Case の default Scope rule で root を決める。

level: MUST

related: [SPEC_018](paths.md#spec_018)

### SPEC_033

Composition 後の effective Scope 群について、filesystem 上の存在を要求せずに path を解決・正規化した Scope root が同一 location になる定義を複数持つことはできない。Default Scope と named Scope の組み合わせにもこの rule を適用する。親子関係にある異なる directory は、この duplicate rule だけでは同一とはみなさない。

level: MUST

condition: composition 後の effective Scope root を検証する場合

### SPEC_034

Selection の Shared reference は、source の origin layer ではなく chain 全体を重ね終えた effective shared namespace で解決する。Outer layer は inner source が参照する同名 pattern set を提供または shadow できる。

level: MUST

## SECTION_403

title: Output と base chain

### SPEC_035

Output definition は source definition のようには compose しない。Configuration は Output を省略でき、共通 definition だけを提供する Base Configuration として利用できる。Archive planning と `--preview` は root Output を必要としない。実際に Archive file を書き込む build で使用するのはルート設定ファイル自身が直接宣言した Output だけとし、root が Output を持たない場合は build error とする。Inner layer の Output を root へ継承しない。

level: MUST

condition: Archive file を書き込む build

### SPEC_036

Base chain 上では、Output を宣言している Configuration の definition だけを各 Configuration の書き込み所有境界として保持し、Output の base-chain write-boundary overlap rules で chain 内の書き込み境界が overlap しないことを検証する。Output を宣言しない layer は write boundary を持たない。

level: MUST
