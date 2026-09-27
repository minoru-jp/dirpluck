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
正本は `devdocs/canonical_sources/python_api/overview.py` です。
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

# Python API overview

この文書は、dirpluck 0.10.x の公式 Python API を説明します。API は CLI と同じ実行 model を Python から利用するための最小 surface として定義し、Configuration parser や builder pipeline の低 level object を一般用途の互換性契約には含めません。

`run()` の引数と runtime modifier は `run.md`、返り値は `result.md`、公開 error boundary は `errors.md`、package root の互換性対象 export は `surface.md` を参照してください。Configuration / Target / Case / Archive の実行意味論は `../specification/INDEX.md` と共通です。

## 位置づけ

公式 API の中心は `dirpluck.run()` です。CLI が受け取る Target、Configuration、Case、Invocation Template、Entry、preview、output modifier を Python argument として渡し、同じ application layer で実行します。

CLI は人間向けの argument parsing、help、exit status、stdout / stderr formatting を担当します。Python API は `SystemExit` を通常の制御手段にせず、結果を `RunResult` で返し、期待される dirpluck error を `DirpluckError` として raise します。

0.10.x では、package root から明示的に export する名前だけを公式 Python API とします。低 level module や underscore 名は implementation detail であり、Beta 中の互換性保証対象には含めません。

## 基本形

```python
import dirpluck

result = dirpluck.run("example")
print(result.output_path)
```

これは概念的に次の CLI invocation と同じです。

```console
dirpluck example
```

`config` を省略した場合は runtime cwd の `default.dirpluck` を使います。Python API では process cwd を変更せずに relative document path の基準だけを指定したい場合、API 専用の `cwd` argument を使えます。

```python
from pathlib import Path
import dirpluck

result = dirpluck.run(
    "example",
    config="configs/review",
    cwd=Path("/work/project"),
)
```

この `config` は `/work/project/configs/review.dirpluck` を選びます。`cwd` は Configuration 内の relative source path の基準を変更しません。それらは通常どおり各 Configuration document location を基準に解決します。
