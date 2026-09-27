<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/python_api/errors.py` です。
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

# DirpluckError

Python API から期待される dirpluck error をまとめて扱う場合は `DirpluckError` を catch します。

```python
import dirpluck

try:
    result = dirpluck.run("example", preview=True)
except dirpluck.DirpluckError as exc:
    print(exc)
```

Invalid Configuration、Target / Selection resolution、Invocation Template、または `run()` の互換でない argument combination は `DirpluckError` の subclass を raise します。CLI の status 2 や `dirpluck: error:` prefix は CLI adapter の presentation であり、Python API contract には含めません。

name: DirpluckError

kind: Type

introduced: 0.9.0
