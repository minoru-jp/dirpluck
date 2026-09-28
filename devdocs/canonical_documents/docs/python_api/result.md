<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/python_api/result.py` です。
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

# RunResult

`preview=True` は Archive file を書き込まず、CLI `--preview` と同じ planning semantics を実行します。Output を解決・書き込みしないため、`output`、`force=True`、`sequence` とは組み合わせません。

```python
result = dirpluck.run("example", preview=True)
print(result.preview_text)
```

`RunResult` は次の public field を持ちます。

```text
output_path         build で生成した ZIP path。preview では None
preview_text        CLI --preview と同じ tree representation
archive_entries     実際に Archive へ入る final entry path の tuple
archive_readme      root README.md として生成する Markdown
skipped_link_count  automatic traversal で除外した link-like entry 数
invocation_empty    選択した Invocation が config / targets / case / archive_mtime を持たなかったか
warnings            non-fatal な planning diagnostic の tuple
```

通常 build でも `preview_text` と `archive_readme` は実際に使用した plan から返します。Planning 中に non-fatal な診断が生じた場合は `warnings` に human-readable message の tuple として返し、CLI も同じ内容を stderr へ表示します。そのため、呼び出し側は CLI output を parse せず、生成結果、plan の主要な public information、移行上重要な warning を取得できます。

name: RunResult

kind: Type

introduced: 0.9.0

output: output_path, preview_text, archive_entries, archive_readme, skipped_link_count, invocation_empty, warnings
