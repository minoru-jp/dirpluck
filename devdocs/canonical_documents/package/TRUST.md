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
正本は `devdocs/canonical_sources/package_trust/canonical.py` です。
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

# dirpluck Trust Quick Reference

この文書は installed package に同梱する compact trust reference です。完全な trust model は同じ release の source distribution にある `docs/TRUST.md`、厳密な互換性契約は `docs/specification/INDEX.md` を参照してください。

## Configuration と Invocation Template

設定ファイルとInvocation Templateはどちらも実行指示です。第三者から受け取った document は、実行前に参照する Configuration、Target、Case、Scope / Always source、Selection、Output を確認してください。dirpluckは、参照先が機密か、description が実態と一致するか、宣言された操作が利用者の目的に対して安全かを推論しません。

## Filesystem boundary

dirpluckは実行 user の OS permission を越えて読み書きしません。一方、user がアクセスでき、Configuration の path rule で参照できる relative `..` や absolute path は source / Output に指定できます。

Configuration / Invocation Template document と明示した Scope / Always root location は host OS の通常の filesystem semantics で解決します。明示 root の内側を自動 traversal するときは、認識した symbolic link / Windows directory junction をたどらず Archive に含めません。FIFO、socket、device など regular file / regular directory でない entry も Archive 対象外です。未知の platform-specific mechanism を完全に列挙・保証するものではありません。

## Selection と preview

Hidden file、repository metadata、environment file、key material などを filename や内容から推論して自動 ignore しません。外部へ渡す Archive では `must` / `may` / `ignore` と実際の生成内容を用途に応じて確認してください。

`--preview` は Archive を書き込まず archive-relative contents plan を確認できます。認識した non-ignored link-like entry を traversal から除外した場合は件数も表示します。

## Output と共有

Output は Configuration または runtime option が宣言した destination と overwrite policy に従います。dirpluckは同じ output path を使う複数 process の lock や競合調停を提供しません。

生成されるアーカイブREADMEは source filesystem path を既定では記録しませんが、`--paths` を使うと absolute path など local environment の情報を含み得ます。README から path を隠すことは Archive contents の inspection / sanitization ではありません。
