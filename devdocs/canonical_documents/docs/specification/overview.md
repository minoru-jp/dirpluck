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
正本は `devdocs/canonical_sources/specification/overview.py` です。
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

# Specification overview

dirpluck の CLI、`.dirpluck` 設定ファイル形式、`.dirpluck-inv` Invocation Template形式について、互換性対象となる厳密な動作意味論を定義する。両 document の内容は TOML syntax を使用する。 Python package root の公式 API surface と `run()` の呼び出し契約は `../python_api/INDEX.md` に定義し、`run()` が実行する Configuration / Target / Case / Invocation / Archive semantics はこの仕様と共通とする。用途は `../../README.md`、用語の意味は `../../GLOSSARY.md`、Configuration の書き方は `../configuration/INDEX.md`、CLI の操作方法は `../cli/INDEX.md`、Configuration / Invocation Template と filesystem 操作の trust boundary は `../TRUST.md` を参照する。

## SECTION_001

title: 公開面

### SPEC_001

互換性を保証する公開面は `dirpluck` CLI、この文書で定義する `.dirpluck` Configuration document / `.dirpluck-inv` Invocation Template document 形式、および `../python_api/INDEX.md` で明示する package-root Python API とする。両 document の内容は TOML syntax を使用する。Package root から明示的に export しない Python module / name は内部実装として扱う。

level: MUST
