from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} 設定ガイド")
class TITLE_1:
    r'''{{TERM_1}} の設定ファイルは、ひとつの抽出意図を記述する TOML ファイルです。この文書は設定を書くためのガイドとして、対象とコンパニオンの選び方、選択定義、ケース、出力方針を説明します。

このモデルを何に使えるかは `README.md`、parser、matching、ファイルシステム、アーカイブ、エラーの厳密な意味論は `SPECIFICATION.md` を参照してください。

## ひとつの抽出意図から始める

再現したいひとつのパッケージに対して、ひとつの設定ファイルを使います。実行ごとに変わる対象、複数ディレクトリに固定された資料、またはその両方を表現できます。

source の構成、コンパニオン path、出力方針が異なる2つの作業は別の設定ファイルにします。ケースはひとつの意図の中で選択を協調して切り替えるためのもので、ひとつの設定を profile の積み重ねへ変えるための機能ではありません。

設定ファイルには次を記述します。

```text
Configuration
├── shared                 optional, named reusable pattern sets
├── target                 optional, runtime-bound
├── companion.<name>       zero or more, configuration-bound
└── output                 exactly one
```

対象またはコンパニオンの少なくとも一方が必要です。

## 対象

実行時に同じ役割の source ディレクトリを1個以上指定したい場合は対象を使います。設定ファイルには1個の `[target]` 定義として何を選ぶかを記述し、実行時ディレクトリ path 自体は保存しません。複数ディレクトリを指定した場合は、同じ対象選択をそれぞれへ独立して適用します。

```toml
[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
```

対象を定義する設定ファイルでは CLI の `DIRECTORY` が1個以上必須です。

```console
{{TERM_1}} submissions/acme
```

同じ対象定義を1回の実行で複数ディレクトリへ適用できます。

```console
{{TERM_1}} submissions/acme submissions/contoso submissions/globex
```

TOML には対象定義を1個だけ記述し、CLI の複数引数が別々の対象定義を作るわけではありません。各 runtime 対象ディレクトリは互いに異なる実ディレクトリへ解決される必要があります。対象を定義しない設定へ位置引数 `DIRECTORY` を渡すとエラーです。これにより、実行時入力と設定ファイルが宣言している source を一致させます。

対象は既定選択、名前付きケース、またはその両方を持てます。ケースだけを持ち `[target]` の既定選択を持たない対象では、実行時に `--case` が必須です。

## コンパニオン

抽出意図そのものに属し、path を TOML へ固定したい source にはコンパニオンを使います。

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

コンパニオン名（上の `guidelines`）は設定内でその source を識別します。`path` は cwd 相対で、ひとつの具体的なディレクトリを指定します。

コンパニオンは対象を必要としません。固定コンパニオンだけで設定を構成できます。

```toml
[companion.contracts]
path = "records/contracts"
description = "Contracts included in the project snapshot."
include = ["*.pdf"]

[companion.minutes]
path = "records/meetings"
description = "Meeting records included in the project snapshot."
include = ["*.md"]

[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
```

この場合は位置引数を指定せずに実行します。

```console
{{TERM_1}} --config project-snapshot
```

## {{TERM_12}}

同じ設定ファイル内で複数の選択から同じ include または exclude パターン集合を使いたい場合は、名前付きの共有パターンを定義できます。共有するのは完全な選択定義ではなくパターン配列だけです。

include 用は `[shared.include_patterns]` に定義します。

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]
```

exclude 用は `[shared.exclude_patterns]` に定義します。

```toml
[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
    "*.pyc",
    ".DS_Store",
]
```

名前付き配列は、それぞれ include または exclude の通常のパターン文法で検証されます。ひとつの名前付き配列は空にできません。定義しただけではどの source にも適用されず、各選択から明示的に参照します。

include 用共有パターンは、必須候補として `include_pattern_refs`、任意候補として `include_if_exists_pattern_refs` から参照します。exclude 用共有パターンは `exclude_pattern_refs` から参照します。

```toml
[target]
description = "The current project for normal development work."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]

[target.case.all]
description = "All project files except shared development artifacts."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"
```

共有参照と選択自身の `include` / `include_if_exists` / `exclude` は併用できます。参照した共有パターンを先に展開し、その後に選択へ直接記述したパターンを追加します。同じ実効パターンが重複した場合は設定エラーです。

ケースは base 選択を継承しないため、共有パターン参照も継承しません。上の例で `python-dev` を base と `all` の両方へ適用したいので、両方が `exclude_pattern_refs = ["python-dev"]` を明示しています。これは Case 継承ではなく、同じ名前付きパターン集合を2つの独立した選択が参照しているだけです。

## 選択フィールド

対象の選択、コンパニオンの base 選択、ケース選択は、それぞれ独立した `description` とファイル選択フィールドを持ちます。直接パターンを記述する代わりに、または直接記述と併用して共有パターンを参照できます。

### `description`

`description` は必須で、空文字列にはできません。ディレクトリ名を言い換えるだけではなく、その source または選択が抽出意図の中で果たす役割を書きます。

```toml
description = "Reference material used to evaluate the submission."
```

生成されるアーカイブ索引にもこの description が記録されるため、用途固有の意味はファイル名から後で推測するのではなくここへ記述します。

### `include`

存在を必須とする項目には `include` を使います。通常ビルドでは各パターンが少なくとも1件一致する必要があります。

```toml
include = [
    "report.pdf",
    "data/*.csv",
]
```

必須パターンが一致しなければエラーです。その項目がないとパッケージが宣言した意図を満たさない場合に使います。

### `include_if_exists`

存在しなくても正常な既知候補には `include_if_exists` を使います。

```toml
include_if_exists = [
    "generated/*.pdf",
    "coverage.xml",
]
```

生成物、任意添付、実行によって存在しないことがあるファイルに使えます。

ひとつの選択で `include` と `include_if_exists` を併用し、必須の中心部分と任意の追加部分を表現することもできます。

### `exclude`

`include` または `include_if_exists` が既に選んだ範囲の名前を除外する場合に `exclude` を使います。

```toml
exclude = [
    ".git/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    ".DS_Store",
    "*.pyc",
]
```

ディレクトリを `include` または `include_if_exists` で選ぶと、その配下は再帰的に収集されます。{{TERM_1}} は隠しファイルや秘密情報らしい名前を自動判定しないため、広い選択ではワークスペースに応じた `exclude` を自分で指定してください。上の一覧は例であり、秘密情報を網羅するものではありません。

`exclude` は別の include 言語ではなく、それ自体でファイルを選択しません。厳密なパターン形式は `SPECIFICATION.md` を参照してください。

### `if_empty`

既定値は次です。

```toml
if_empty = "error"
```

`include_if_exists` だけを持つ選択では、0件の最終結果を明示的に許可できます。

```toml
include_if_exists = ["generated/*.pdf"]
if_empty = "allow"
```

`if_empty = "allow"` は必須の `include`、または `include_pattern_refs` による必須共有 include と併用できません。

## ケース

ケースは設定ファイル全体で共有する1個の平坦な名前付き選択 variation です。一回の実行で有効にできるケース名は最大1個です。

ケースは source の選択全体を置き換えます。base 選択を継承したり merge したりしません。base が参照している共有パターンも暗黙には引き継がないため、必要なケースは同じ共有名を自分で参照します。

### 対象ケース

```toml
[target]
description = "The current project for normal development work."
include = ["src", "pyproject.toml"]

[target.case.review]
description = "The current project with review material included."
include = ["src", "tests", "pyproject.toml"]
```

```console
{{TERM_1}} project-a project-b --case review
```

対象がある場合、有効なケース名は対象が定義します。`review` を選ぶなら `[target.case.review]` が必要で、その同じケース選択を CLI から渡したすべての runtime 対象へ適用します。

### コンパニオンケースとフォールバック

設定全体のケースに合わせてコンパニオンの選択も変える場合は、同名ケースを定義します。

```toml
[companion.framework]
path = "framework"
description = "The framework used by the project."
include = ["dist/framework-*.whl"]

[companion.framework.case.review]
description = "The framework distribution and source used during review."
include = ["dist/framework-*.whl", "src"]
```

`--case review` が有効なら、このコンパニオンは `review` 選択を使います。同名ケースを持たないコンパニオンは削除されず、base 選択へフォールバックします。

### 対象を持たないケース

コンパニオンだけの設定でもケースを使えます。

```toml
[companion.documents]
path = "documents"
description = "Current documents in the snapshot."
include = ["current/*.md"]

[companion.documents.case.archive]
description = "Current and historical documents in the archival snapshot."
include = ["current/*.md", "history/*.md"]

[companion.assets]
path = "assets"
description = "Assets included in every snapshot."
include = ["*.png"]
```

```console
{{TERM_1}} --config snapshot --case archive
```

この場合 `documents` は `archive` ケース、`assets` は base を使います。対象がない設定でケースを選ぶ場合は、少なくとも1個のコンパニオンがそのケースを定義している必要があります。

ケース名は平坦です。ケースを組み合わせたり、`--case` を複数回指定したり、`case.review.case.security` のように多階層化したりしません。

ケースが変更できるのは選択だけです。別のコンパニオン集合、別のコンパニオン path、別の出力方針が必要なら別の設定ファイルを使います。

## 出力

すべての設定ファイルはひとつの `[output]` を持ちます。出力は、ひとつの既知 path を更新する**固定出力**か、実行ごとに時刻を含む新しい名前を作る**動的命名出力**のどちらかです。2つの形式は混在できません。

### 固定出力

```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`path` は cwd 配下の具体的な path です。`if_exists` は必須で、次のどちらかを指定します。

- `error` は既存出力を置き換えずに失敗します。
- `overwrite` は新しいアーカイブが正常に書き終わった後だけ既存出力を置き換えます。

既知のひとつの成果物を更新したい場合に使います。上書きを許可できるのはこの形式だけです。

### 動的命名出力

スナップショットや定例パッケージのように、実行結果を蓄積したい場合は出力ディレクトリと命名要素を記述します。

```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "review"
```

ファイル名は次の固定順序で生成します。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

上の設定なら、たとえば次の名前になります。

```text
project-20260916-011623-review.zip
```

`prefix` と `suffix` は省略できます。`timestamp = true` は必須で、実行プロセスのローカル時刻をビルド開始時に一度だけ確定して使います。自由な時刻書式やテンプレート文字列は指定しません。

同じ秒に複数の実行を明示的に区別したい場合は、CLI から正の整数を渡せます。

```console
{{TERM_1}} --config project-snapshot --sequence 3
```

この場合、番号は timestamp の直後に入ります。

```text
project-20260916-011623-3-review.zip
```

`--sequence` は自動採番ではありません。{{TERM_1}} は既存ファイルから次の番号を推測せず、指定されなければ番号部分を付けません。固定出力では `--sequence` を指定できません。

動的命名出力では `if_exists` を指定できず、確認時点で生成された名前が既に存在すればエラーです。自動採番や自動リネームは行いません。{{TERM_1}} は同じ出力 path への並行書き込みを調停しないため、実行が重なる可能性がある場合は呼び出し側が異なる名前を与える必要があります。

出力形式自体を CLI から一時 override しません。出力方法が異なる2つの作業は別の設定ファイルとして表します。`--sequence` は動的命名規則を置き換えるものではなく、その規則が用意する実行時の番号位置だけを埋めます。

## 完全な例: 変化する対象と固定参照資料

```toml
[shared.exclude_patterns]
workspace-noise = [
    ".git/",
    "__pycache__/",
    "*.pyc",
]

[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
include_if_exists = ["attachments"]
exclude_pattern_refs = ["workspace-noise"]

[target.case.audit]
description = "The submission with additional records required for audit."
include = [
    "documents",
    "metadata.json",
    "records",
]
include_if_exists = ["attachments"]
exclude_pattern_refs = ["workspace-noise"]

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[companion.guidelines.case.audit]
description = "Guidelines and audit checklist used for an audit review."
include = ["*.md", "audit-checklist.pdf"]

[companion.reference]
path = "reference-data"
description = "Reference data used by every review type."
include = ["*.csv"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

通常のレビュー。対象ディレクトリは1個以上指定できます。

```console
{{TERM_1}} submissions/acme submissions/contoso
```

監査用 variation:

```console
{{TERM_1}} submissions/acme submissions/contoso --case audit
```

同じ対象選択を両方の runtime 対象へ適用します。`audit` ではすべての runtime 対象と `guidelines` が `audit` に切り替わり、`reference` は `audit` ケースを持たないため base を使います。

## 完全な例: 固定 source のスナップショット

```toml
[companion.documents]
path = "records/documents"
description = "Documents that define the current project state."
include = ["*.pdf", "*.md"]

[companion.decisions]
path = "records/decisions"
description = "Recorded decisions that explain the current project state."
include = ["*.md"]

[companion.generated]
path = "generated"
description = "Generated material available at snapshot time."
include_if_exists = ["*.pdf", "*.zip"]
if_empty = "allow"

[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "snapshot"
```

```console
{{TERM_1}} --config project-snapshot
```

すべての source が固定コンパニオンなので、この設定ファイルは対象なしで完結します。実行ごとに `project-YYYYMMDD-HHMMSS-snapshot.zip` が追加されます。同じ秒にスクリプトから複数生成する場合だけ、呼び出し側が `--sequence N` を明示できます。

## 設定探索

既定では `{{TERM_1}}.toml` を探索します。`--config NAME` では `.toml` を省略できます。

```console
{{TERM_1}} DIRECTORY [DIRECTORY ...] --config review
```

設定探索は cwd と `./{{TERM_1}}/` の直下だけで行います。同じ名前が両方に存在する場合は優先順位で解決せず、曖昧としてエラーにします。

次のコマンドで検出可能な設定を列挙できます。

```console
{{TERM_1}} --configs
```

## 厳密な構文と実行規則

この文書は設定をどう構成して書くかを説明します。`SPECIFICATION.md` は include / exclude の厳密なパターン文法、case-sensitive matching、シンボリックリンク境界、アーカイブ path、dry-run、validation error の最終的な規範です。
'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_12,)
