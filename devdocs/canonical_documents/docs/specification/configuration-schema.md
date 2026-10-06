<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/configuration_schema.py` です。
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

# Configuration schema

## SPEC_011

受理する top-level 構造は次とする。

```text
[about]
[shared.must]
[shared.may]
[shared.ignore]
[pluck]
[case.pluck.<name>]
[case.always.<name>]
[scope]
[scope.<name>]
[layout.<name>]
[namespace.<name>]
[always.<name>]
[extra.<name>]
[output]
[output.timestamp]
```

level: MUST

## SPEC_012

未知の key は error とする。

level: MUST

## SPEC_013

`[about]` は任意で、`description` / `description_no_targets` / `description_no_always` / `description_empty` / `always_layout` / `targets_layout` / `base` を持てる。各 field は任意だが、`[about]` を定義する場合は少なくとも1 field を必要とする。4つの description field は空でない string とする。`always_layout` / `targets_layout` は1個の Archive directory component として有効な Layout name reference、`base` は1個の Configuration file path とする。

level: MUST

condition: `[about]` を定義する場合

## SPEC_014

Base chain を構成する各 Configuration は Pluck を0個または1個、名前付き Scope、Layout、Always source、Extra source、Shared pattern、ネームスペースを0個以上持てる。`[scope]` は root Configuration で常設される default Scope の optional `description` / `target_kind` / `ignore` / `layout` / `namespace` 設定であり、Scope の存在宣言ではない。Named Scope は required `path` と同じ optional field を持つ。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` とする。`[layout.<name>]` は Archive 内の最上位 directory を宣言する名前付き definition で、optional `description` だけを持てる。`description` を省略した空 table も valid とし、親 `[layout]` だけを定義して名前付き Layout を1個も持たない Configuration は error とする。Layout name は TOML key として解釈した後に1個の Archive directory component として検証し、同一 Configuration 内で大文字小文字を区別しない比較で一意でなければならない。Canonical `[always.<name>]` と `[extra.<name>]` は同じ source schema を持ち、required `path`、Selection field、optional `layout` を持つ。`namespace` は 1.0 schema に含めない。Always source は定義された時点で参加候補になるが、Extra source は定義だけでは inactive とし、`[case.always.<name>].include` の完全指定または `add` の差分指定で参照された run だけ Always source と同じ fixed source role で参加する。Case definition は top-level `[case]` namespace の下に置き、`[case.pluck.<name>]` は Pluck の完全な Selection、`[case.always.<name>]` は effective Always / Extra source 集合の participation rule とする。これにより `case` は Always source 名として予約せず、`[always.case]` は通常の Always source definition として使用できる。

level: MUST

## SPEC_015

各 Configuration は Output を0個または1個宣言できる。Output を宣言する場合、fixed output と timestamp output は排他的である。Configuration file 単体の schema validity と Archive planning / `--preview` には Output を要求しない。Archive file を書き込む build では、ルート設定ファイル自身の Output declaration または runtime Output のどちらかを必要とする。Base Configuration の Output は Root Configuration へ継承しない。

level: MUST

condition: Output を宣言する場合, Archive file を書き込む build

## SPEC_016

各 Configuration と Base composition 後の実効設定は source definition を1個も持たなくてもよい。Pluck、Always source、Extra source、named Scope はすべて optional であり、常設の default Scope だけを持つ Effective Configuration も valid とする。Runtime request の結果として resolved source が0個でも build / preview は正常に成立し、Archive は generated `README.md` だけを含められる。

level: MUST

condition: Base composition 後
