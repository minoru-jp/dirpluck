<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/__init__.py` です。
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

# dirpluck Specification

| Document | Summary |
| --- | --- |
| [Specification overview](overview.md) | 仕様全体の位置づけ、公開面、関連文書への導線。 |
| [CLI document selection](document-selection.md) | Configuration と Invocation Template の選択・解決規則。 |
| [Configuration schema](configuration-schema.md) | Configuration document の top-level schema と table 構造。 |
| [Filesystem path notation](paths.md) | Configuration と runtime input で使用する filesystem path notation。 |
| [Base chain and composition](composition.md) | Base chain、cycle detection、definition composition、Output の扱い。 |
| [Runtime Target, Scope, and Case](runtime-targets.md) | Scope、Target reference、expansion、Always source、Case の解決規則。 |
| [Namespace](namespace.md) | Archive placement に使用する Namespace の canonical semantics。 |
| [Selection and shared patterns](selection.md) | Selection、Shared pattern、include/ignore pattern grammar。 |
| [Filesystem boundary and entry types](filesystem.md) | filesystem boundary、link-like entry、non-regular entry の扱い。 |
| [Archive planning](archive.md) | final archive root、entry collision、generated README の planning 規則。 |
| [Output](output.md) | fixed/timestamp/runtime Output、overwrite、collision 規則。 |
| [Preview](preview.md) | preview mode の出力と副作用境界。 |
| [CLI contract](cli-contract.md) | CLI options、組み合わせ制約、exit behavior の契約。 |
| [Pre-1.0 compatibility](compatibility.md) | 1.0.0 で削除することが確定している pre-1.0 compatibility input / behavior。 |
