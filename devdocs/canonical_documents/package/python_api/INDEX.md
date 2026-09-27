<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "devdocs.canonical_sources.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/python_api/__init__.py` です。
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

# dirpluck Python API

| Document | Summary |
| --- | --- |
| [Python API overview](overview.md) | 公式 Python API の位置づけ、基本的な呼び出し方、互換性境界。 |
| [dirpluck.run](run.md) | high-level `run()` entry point と runtime modifier の契約。 |
| [RunResult](result.md) | preview/build の結果として返す `RunResult` とその公開 field。 |
| [DirpluckError](errors.md) | Python API が公開する error boundary と `DirpluckError`。 |
| [Package surface](surface.md) | package root の公式 export と内部実装との互換性境界。 |
