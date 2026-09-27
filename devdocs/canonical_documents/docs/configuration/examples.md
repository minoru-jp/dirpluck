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
正本は `devdocs/canonical_sources/configuration/examples.py` です。
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

# Configuration examples

この文書は、主要な Configuration 要素を組み合わせた complete example を示します。

この文書は複数の authoring concern を一つに組み合わせた例です。各 field の説明はこの Configuration collection、厳密な契約は `../specification/INDEX.md`、CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` を参照してください。

## Complete example

```toml
[about]
description = "Materials prepared for reviewing the current project."
base = "../common/common.dirpluck"

[shared.ignore]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [["python-dev"]]
allow_empty = true

[pluck.case.full]
description = "The project with all review material."
may = ["README.md", "src", "tests", "docs"]
ignore = [["python-dev"]]
allow_empty = true

[scope]
ignore = ["archive"]

[scope.projects]
path = "/srv/projects"
ignore = ["archive", "tmp-*"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

```console
dirpluck projects/example
dirpluck projects/example --case full --preview
dirpluck projects/
```

CLI の全 option と Configuration / Invocation Template の選択方法は `../cli/INDEX.md`、この Configuration が正確にどう解決・検証されるかは `../specification/INDEX.md` を参照してください。
