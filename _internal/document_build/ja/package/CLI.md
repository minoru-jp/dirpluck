<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `dirpluck_docs/package_cli/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `_internal/document_build/ja/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck CLI Quick Reference

wheel に同梱する最小 CLI reference です。

```text
dirpluck [DIRECTORY ...] [--config NAME] [--case NAME] [--sequence N] [--dry-run] [--paths]
dirpluck --configs
dirpluck --version
```

- Effective Configuration に Target がある場合は1個以上の `DIRECTORY` を指定します。Target がない場合は指定しません。
- `--config NAME` は cwd と `./dirpluck/` から Configuration filename を選びます。`.toml` は省略できます。
- `--case NAME` は named Case を1個選びます。
- `--dry-run` は archive を書き込まず ZIP contents の plan を表示します。
- `--paths` は生成される Archive README に解決済み source filesystem path を追加します。既定では path を記録しません。
- `--sequence N` は generated output name の明示的な正整数 sequence です。自動採番ではありません。
- `--configs` は cwd から検出できる Configuration を一覧表示して終了します。

```console
dirpluck projects/example --dry-run
dirpluck projects/example --case audit
dirpluck --config snapshot
```

TOML の最小 reference は同梱の `CONFIGURATION.md` を参照してください。より詳しい CLI semantics、Configuration guide、Glossary、Specification は同じ release の source distribution にある `docs/CLI.md`, `docs/CONFIGURATION.md`, `GLOSSARY.md`, `docs/SPECIFICATION.md`, `docs/TRUST.md` を参照してください。
