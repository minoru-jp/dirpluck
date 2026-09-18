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
正本は `dirpluck_docs/usage/canonical.py` です。
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

# dirpluck 使用ガイド

実行時に必要な操作規則だけを示します。

## 基本

- 公開インターフェースは CLI と TOML Configuration。
- 新規または変更した Configuration は、通常実行の前に `--dry-run` で確認する。
- 既定のルート設定ファイルは cwd または `./dirpluck/` の `dirpluck.toml`。
- `--config NAME` は cwd または `./dirpluck/` からルート設定ファイルを選ぶ。`.toml` は省略可能。
- ルート設定ファイル自身の `[target]` が実効設定へ残る場合だけ1個以上の `DIRECTORY` を渡す。
- import 由来 Target が実効 Targetになる場合、または Target がない場合は `DIRECTORY` を渡さない。

```console
dirpluck PROJECT --dry-run
dirpluck PROJECT
dirpluck PROJECT --config review --dry-run
dirpluck --config snapshot --dry-run
```

Case を使う場合:

```console
dirpluck PROJECT --case all --dry-run
```

## Target

必ず存在する項目:

```toml
[target]
description = "The current project."
include = [
    "pyproject.toml",
    "src",
]
```

存在する場合だけ取得する項目:

```toml
[target]
description = "The current project."
include_if_exists = [
    "README.md",
    "tests",
    "docs",
]
if_empty = "allow"
```

Target 全体を取得し、空でも許可する場合:

```toml
[target]
description = "The current project."
include_if_exists = ["*"]
if_empty = "allow"
```

ディレクトリが include に一致すると、その配下のファイルも再帰的に収集される。

## 除外

```toml
exclude = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

広い include を使う場合は、用途に応じて必要な除外を明示する。

## 共有パターン

共有 exclude:

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

参照:

```toml
[target]
description = "The current project."
include_if_exists = ["src", "tests"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

共有 include:

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]
```

必須候補として参照:

```toml
include_pattern_refs = ["project-core"]
```

任意候補として参照:

```toml
include_if_exists_pattern_refs = ["project-core"]
```

共有パターンは定義しただけでは適用されない。使用する Selection から明示的に参照する。

Configuration chain では共有パターン名も内側から外側へ解決する。通常の名前を参照し、外側の同名定義が内側を shadow する。

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"

[shared.exclude_patterns]
python-dev = [".git/", ".venv/", "__pycache__/", "*.pyc"]

[target]
description = "The current project."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Selection が内側 Configuration にあっても、`python-dev` は最終的な実効設定の shared namespace で解決される。外側 layer は同名共有パターンを提供または override できる。

## Case

```toml
[target.case.all]
description = "All target files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

Case は base Selection を継承しない。必要な `include`、`include_if_exists`、`exclude`、共有パターン参照は Case 側にも明示する。

## Companion

```toml
[companion.tool]
path = "tool-project"
description = "A related project used with the target."
include = ["dist/tool-*.whl"]
```

選択中の Case と同名の Companion Case があればそれを使う。なければ Companion の base Selection を使う。

## 設定インポート

別の Configuration を取り込む場合:

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

- 各 Configuration が持てる `[import.<name>]` は0個または1個。
- import 先もさらに1個 import できる。chain の長さに上限はない。
- 同じ Configuration file が現在の chain に再登場したら循環参照エラー。
- `root` はその import を記述した Configuration file の所在ディレクトリ相対。`/` 区切りを使い、`..` は使用できる。絶対 path は使用しない。
- `configuration` は import root 内の相対 TOML file path。探索は行わない。
- 名前解決は最深部から最外側。外側の同名 Target / Companion / shared pattern が内側を shadow する。
- import 名は link 識別用で、Companion や shared pattern へ自動 prefix を付ける namespace ではない。
- `[import.<name>.case]` は使わない。CLI `--case` を実効設定全体へ1個だけ適用する。
- import 先の `[output]` は実行しない。最終出力はルート設定ファイルの `[output]` だけ。

直下 import root を基準に Companion を追加・overrideする場合:

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

この Companion は通常の名前 `project` で名前解決へ参加する。`path = "."` で import root 自体を Companion にできる。

Import 由来 Target が実効設定へ残る場合、Target を定義した Configuration は次のどちらかに配置する。

```text
<project>/dirpluck.toml
<project>/dirpluck/<name>.toml
```

この配置から `<project>` を対象 directory として解決する。Root 側 Target が同名 singleton `target` を定義すれば、import 由来 Target とその Case は使用されない。

## Output

固定名:

```toml
[output]
path = "output.zip"
if_exists = "overwrite"
```

既存ファイルを拒否する場合は `if_exists = "error"` を使う。

時刻ベースの生成名:

```toml
[output]
directory = "dist"
prefix = "context"
timestamp = true
suffix = "dev"
```

必要な場合だけ正の sequence を明示する。

```console
dirpluck PROJECT --sequence 2
```

## 運用

- `--dry-run` で選択内容を確認してから通常実行する。
- `[missing]` は必須 `include` の未一致として確認する。
- `[optional missing]` は `include_if_exists` の未一致として、意図した結果か確認する。
- ルート設定ファイルは cwd、各 import layer は対応する `root` を filesystem boundary として扱う。
- import を追加・変更した場合は `--dry-run` で chain、shadow 結果、Target directory、Companion を確認する。
- symlink を含む構成では `--dry-run` で解決結果を確認する。

## 間違えやすい点

- `include` は必須。存在しないことが正常な候補には `include_if_exists` を使う。
- 空の Target に `include = ["*"]` を使うと必須パターン未一致になる。空を許す場合は `include_if_exists = ["*"]` と `if_empty = "allow"` を使う。
- `if_empty = "allow"` は必須 `include` を持つ Selection には使えない。
- Case は base の selection field や共有パターン参照を継承しない。
- 共有パターンは自動適用されない。
- include 用と exclude 用の共有パターンは別々に定義する。
- 1つの Configuration に複数の `[import.<name>]` を定義しない。
- import depth に上限はないが、循環参照は許可されない。
- import 名を shared pattern / Companion の prefix として扱わない。
- import 由来 Target が実効 Targetの場合は CLI `DIRECTORY` を渡さない。
- import chain 内側の `[output]` は実行されない。
- 通常の Target / Companion に `..` を使って boundary を広げない。別 Configuration を使う場合は `[import.<name>]` を使う。
- Python 内部モジュールを公開 API として使用しない。

## 詳細

sdist またはリポジトリを参照できる場合に、必要に応じて次を確認する。

- `CONFIGURATION.md`: TOML Configuration の詳細
- `SPECIFICATION.md`: 厳密な動作仕様
- `GLOSSARY.md`: 用語
- `README.md`: ライブラリ全体の説明
