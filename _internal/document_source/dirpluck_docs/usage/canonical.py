from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} 使用ガイド")
class TITLE_1:
    r'''実行時に必要な操作規則だけを示します。

## 基本

- 公開インターフェースは CLI と TOML Configuration。
- 新規または変更した Configuration は、通常実行の前に `--dry-run` で確認する。
- 既定の{{TERM_14}}は cwd または `./dirpluck/` の `dirpluck.toml`。
- `--config NAME` は cwd または `./dirpluck/` から{{TERM_14}}を選ぶ。`.toml` は省略可能。
- `[target]` がある Configuration では1個以上の `DIRECTORY` を渡す。
- Companion だけの Configuration では `DIRECTORY` を渡さない。

```console
{{TERM_1}} PROJECT --dry-run
{{TERM_1}} PROJECT
{{TERM_1}} PROJECT --config review --dry-run
{{TERM_1}} --config snapshot --dry-run
```

Case を使う場合:

```console
{{TERM_1}} PROJECT --case all --dry-run
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

## {{TERM_13}}

別の Configuration を取り込む場合:

```toml
[import.shikumi-stack]
root = ".."
configuration = "shikumi/dirpluck.toml"
case = "distribution"

[import.shikumi-stack.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

- `root` は {{TERM_14}}自身の所在ディレクトリ相対。`/` 区切りを使い、import では `..` を使用できる。絶対 path は使用しない。
- `configuration` は import root 内の相対 TOML file path。探索は行わない。
- import 先から使用するのは Companion だけ。Target は使用しない。
- 必要なら `[import.<name>.companion.<name>]` を追加し、import root 内の source を Root 側から Companion として定義する。
- import 配下の論理名は `<import>.<companion>`。import 先設定由来と Root 側追加で同名 Companion を定義しない。
- Root 側追加 Companion の `path` は import root 相対。`path = "."` で import root 自体を Companion にできる。絶対 path と `..` は使用しない。
- Root 側追加 Companion の shared pattern 参照は Root Configuration の `[shared.*]` を使う。import 先設定由来 Companion は import 先の `[shared.*]` を使う。
- import 先設定由来または Root 側追加を合わせて少なくとも1個の Companion が必要。
- `case` は import 名前空間の Companion 群だけに適用する。少なくとも1個の Companion がその Case を定義している必要がある。Root の `--case` は伝播しない。
- import 先の `[output]` は使用しない。最終出力は{{TERM_14}}の `[output]` だけ。
- import 先 Configuration からさらに import しない。0.3.0 は1階層だけ。

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
{{TERM_1}} PROJECT --sequence 2
```

## 運用

- `--dry-run` で選択内容を確認してから通常実行する。
- `[missing]` は必須 `include` の未一致として確認する。
- `[optional missing]` は `include_if_exists` の未一致として、意図した結果か確認する。
- {{TERM_14}}は cwd、import 先は各 import の `root` を filesystem boundary として扱う。
- import を追加・変更した場合も `--dry-run` で root、Configuration、Companion の解決結果を確認する。
- symlink を含む構成では `--dry-run` で解決結果を確認する。

## 間違えやすい点

- `include` は必須。存在しないことが正常な候補には `include_if_exists` を使う。
- 空の Target に `include = ["*"]` を使うと必須パターン未一致になる。空を許す場合は `include_if_exists = ["*"]` と `if_empty = "allow"` を使う。
- `if_empty = "allow"` は必須 `include` を持つ Selection には使えない。
- Case は base の selection field や共有パターン参照を継承しない。
- 共有パターンは自動適用されない。
- include 用と exclude 用の共有パターンは別々に定義する。
- {{TERM_14}}の CLI `DIRECTORY` と `--case` は import 先へ自動伝播しない。
- import 先の Target は使用されない。
- import 先の `[output]` は実行されない。
- import 先に `[import.<name>]` を持たせない。
- 通常の Target / Companion に `..` を使って boundary を広げない。別 Configuration を使う場合は `[import.<name>]` を使う。
- Python 内部モジュールを公開 API として使用しない。

## 詳細

sdist またはリポジトリを参照できる場合に、必要に応じて次を確認する。

- `CONFIGURATION.md`: TOML Configuration の詳細
- `SPECIFICATION.md`: 厳密な動作仕様
- `GLOSSARY.md`: 用語
- `README.md`: ライブラリ全体の説明
'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_13, terms.TERM_14,)
