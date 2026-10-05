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
[namespace.<name>]
[always.<name>]
[output]
[output.timestamp]
```

level: MUST

## SPEC_012

未知の key は error とする。

level: MUST

## SPEC_013

`[about]` は任意で、`description` と `base` だけを持つ。両 field はそれぞれ任意だが、`[about]` を定義する場合は少なくとも一方を必要とする。`description` は空でない string、`base` は1個の Configuration file path とする。

level: MUST

condition: `[about]` を定義する場合

## SPEC_014

Base chain を構成する各 Configuration は Pluck を0個または1個、名前付き Scope、Always source、Shared pattern、ネームスペースを0個以上持てる。`[scope]` は root Configuration で常設される default Scope の optional `description` / `target_kind` / `ignore` / `namespace` 設定であり、Scope の存在宣言ではない。Named Scope は required `path` と同じ optional field を持つ。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかで、既定は `"directory"` とする。Canonical `[always.<name>]` は required `path` と Selection field だけを持ち、`namespace` は 1.0 schema に含めない。Case definition は top-level `[case]` namespace の下に置き、`[case.pluck.<name>]` は Pluck の完全な Selection、`[case.always.<name>]` は effective Always source 集合の membership filter とする。これにより `case` は Always source 名として予約せず、`[always.case]` は通常の Always source definition として使用できる。

level: MUST

## SPEC_015

各 Configuration は Output を0個または1個宣言できる。Output を宣言する場合、fixed output と timestamp output は排他的である。Configuration file 単体の schema validity と Archive planning / `--preview` には Output を要求しない。Archive file を書き込む build では、ルート設定ファイル自身の Output declaration または runtime Output のどちらかを必要とする。Base Configuration の Output は Root Configuration へ継承しない。

level: MUST

condition: Output を宣言する場合, Archive file を書き込む build

## SPEC_016

各 Configuration と Base composition 後の実効設定は source definition を1個も持たなくてもよい。Pluck、Always source、named Scope はすべて optional であり、常設の default Scope だけを持つ Effective Configuration も valid とする。Runtime request の結果として resolved source が0個でも build / preview は正常に成立し、Archive は generated `README.md` だけを含められる。

level: MUST

condition: Base composition 後
