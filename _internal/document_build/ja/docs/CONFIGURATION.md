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
正本は `dirpluck_docs/configuration/canonical.py` です。
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

# dirpluck Configuration Guide

この文書は、設定ファイルを TOML で書くためのガイドです。各 field の厳密な validation、pattern grammar、import resolution、filesystem boundary などは `SPECIFICATION.md`、Configuration の選択方法と CLI option は `CLI.md` を参照してください。

## 基本形

Configuration はひとつの最終アーカイブ意図を表します。最小構成では source と output を定義します。

```toml
[companion.notes]
path = "notes"
description = "Notes included in the package."
include = ["*.md"]

[output]
path = "artifacts/notes.zip"
if_exists = "overwrite"
```

実行ごとに変わる source がある場合は対象、Configuration に path を固定する source はコンパニオンとして表します。必要に応じて共有パターン、ケース、設定インポートを追加します。

## Target

Target は実行時に CLI から与える source directory へ同じ選択規則を適用するときに使います。

```toml
[target]
description = "The submission currently being reviewed."
include = ["documents", "metadata.json"]
include_if_exists = ["attachments"]
exclude = [".git/", "__pycache__/", "*.pyc"]
```

実際の Target directory は Configuration に書きません。CLI から1個以上与えた directory へ同じ Target selection が独立して適用されます。

```console
dirpluck submissions/acme submissions/contoso
```

Target がない Configuration では positional `DIRECTORY` は使いません。

## Companion

Companion は Configuration 側で source directory を固定するときに使います。

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

複数の Companion は名前を変えて定義します。Companion だけで完結する Configuration も有効です。

## Selection

Target、Companion、Case はそれぞれ独立した selection を持ちます。selection では `description` と、include 候補を記述します。

### `description`

その source が抽出意図の中で果たす役割を書きます。生成されるアーカイブREADMEにも使われるため、単なる directory 名ではなく意味を記述してください。

```toml
description = "Reference material used to evaluate the submission."
```

### `include`

存在が必要な候補です。

```toml
include = ["report.pdf", "data/*.csv"]
```

### `include_if_exists`

存在しないことが正常な候補です。

```toml
include_if_exists = ["generated/*.pdf", "coverage.xml"]
```

`include` と `include_if_exists` は同じ selection で併用できます。

### `exclude`

既に include 候補として選んだ範囲から、名前で除外するときに使います。

```toml
exclude = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

ディレクトリを include すると配下も収集対象になります。dirpluck は秘密情報らしい名前を自動判定しないため、広い directory 選択では workspace に必要な除外を明示してください。

### `if_empty`

任意候補だけの selection で、0 file を正常としたい場合に使います。

```toml
include_if_exists = ["generated/*.pdf"]
if_empty = "allow"
```

既定は `"error"` です。組み合わせ可能な field の厳密な条件は `SPECIFICATION.md` を参照してください。

## Shared patterns

同じ include / exclude 配列を複数 selection で使う場合は共有パターンとして名前を付けます。

```toml
[shared.include_patterns]
project-core = ["pyproject.toml", "src", "README.md"]

[shared.exclude_patterns]
python-dev = [".git/", ".venv/", "__pycache__/", "*.pyc"]

[target]
description = "The current project."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]
```

Shared pattern は参照した selection にだけ適用されます。直接記述した `include` / `include_if_exists` / `exclude` と組み合わせることもできます。

Import を使う場合の shared pattern name resolution は `SPECIFICATION.md` で定義します。

## Cases

ケースは、同じ source に別の完全な selection を用意するときに使います。

```toml
[target]
description = "Normal review."
include = ["documents", "metadata.json"]

[target.case.audit]
description = "Audit review."
include = ["documents", "metadata.json", "records"]
```

```console
dirpluck submissions/acme --case audit
```

Case は base selection への差分ではありません。Case で必要な include / exclude / shared pattern reference は Case 自身へ書きます。

Target と Companion が同じ Case 名を持てば、同じ CLI `--case` で対応する variation を選べます。Companion に同名 Case がない場合の扱いなど、正確な Case semantics は `SPECIFICATION.md` を参照してください。

## Configuration import

既存の Configuration を内側の layer として再利用するときは設定インポートを使います。

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

`root` はこの import を書いた Configuration file の所在 directory からの相対 path、`configuration` は解決した import root 内の TOML file path です。

Import された definition と現在の Configuration の definition から実効設定が構成されます。同名 definition がある場合の shadowing、chain、cycle、shared pattern resolution の正確な規則は `SPECIFICATION.md` にまとめています。

Import 先の Target が実効設定へ残る場合でも、実際の Target directory は CLI `DIRECTORY` から与えます。Import 先 Configuration file の directory を Target directory として推論しません。

Import root 内の固定 source を親側から Companion として追加したい場合は overlay を使えます。

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The imported project itself."
include_if_exists = ["pyproject.toml", "src", "README.md"]
if_empty = "allow"
```

## Output

各 Configuration は `[output]` を持ちます。固定 path を更新する形式と、timestamp 付きの名前を作る形式があります。

### Fixed output

```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`if_exists` は `"error"` または `"overwrite"` です。ひとつの既知 artifact を更新する用途に向きます。

### Generated output

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "snapshot"
```

定例 snapshot のように run ごとに artifact を蓄積する用途に向きます。同じ秒に複数 run を意図的に開始する場合は CLI `--sequence N` を使えます。

Filename layout、collision、concurrent write、inner Configuration の output の扱いは `SPECIFICATION.md` を参照してください。

## Complete example

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]

[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[target.case.full]
description = "The project with all review material."
include_if_exists = ["README.md", "src", "tests", "docs"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
dirpluck projects/example
dirpluck projects/example --case full --dry-run
```

CLI の全 option と Configuration discovery は `CLI.md`、この Configuration が正確にどう解決・検証されるかは `SPECIFICATION.md` を参照してください。
