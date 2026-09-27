<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/namespace.py` です。
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

# Namespace

## SPEC_061

ネームスペースは `[namespace.<name>]` という名前付き table で定義する。現行 schema では table 本体は空でなければならず、属性を受理しない。親 `[namespace]` だけを空で定義することは Namespace definition にならないため error とする。

level: MUST

## SPEC_062

Namespace name はそのまま ZIP 内の directory component になる。空名、`.`、`..`、`/`、backslash、control character、portable filename component として不適切な `< > : " | ? *` を拒否する。Namespace は filesystem path ではなく Archive path の1 component である。

level: MUST

## SPEC_063

Scope / Always source の `namespace` field は effective Namespace name を参照する。Namespace を参照した source の final archive root は `NAMESPACE/SOURCE_ROOT` とする。この prefix は他 source との衝突有無にかかわらず常に適用する。Namespace を参照しない source の final archive root は `SOURCE_ROOT` のままとする。

level: MUST

## SPEC_064

複数 source が同じ Namespace を参照すること自体は有効である。ただし Namespace は自動 collision resolver ではなく、final archive root の一意性は Archive planning の final archive root uniqueness rule で検証する。

level: MAY
