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

# dirpluck 設定ガイド

dirpluck の設定ファイルは、抽出意図を記述する TOML ファイルです。この文書は設定を書くためのガイドとして、対象とコンパニオンの選び方、別の設定ファイルを明示的に取り込む方法、選択定義、ケース、出力方針を説明します。

このモデルを何に使えるかは `README.md`、parser、matching、ファイルシステム、アーカイブ、エラーの厳密な意味論は `SPECIFICATION.md` を参照してください。

## ひとつの抽出意図から始める

再現したいひとつのパッケージに対して、ひとつのルート設定ファイルを使います。必要なら別の Configuration を1個だけ import でき、その import 先もさらに1個だけ import できます。dirpluck はこの linear chain を最深部から外側へ解決して実効設定を作ります。

設定ファイルには次を記述できます。

```text
Configuration
├── shared                 optional, named reusable pattern sets
├── import.<name>          zero or one
│   └── companion.<name>  zero or more, overlays anchored to import root
├── target                 optional, at most one per Configuration
├── companion.<name>       zero or more
└── output                 exactly one
```

各 Configuration が持てる `[import.<name>]` は最大1個です。複数 import を同じ層に並べません。import の深さには上限を設けず、同じ Configuration file が現在の chain に再登場した場合だけ循環参照としてエラーにします。

Target、Companion、共有パターンは import 先から import 元へ名前解決します。外側に同名定義があれば内側の定義全体を shadow します。Target は各 Configuration で最大1個なので、最終的な実効設定でも最大1個です。Companion と共有パターンは異なる名前を蓄積し、同名だけを外側が置き換えます。`[output]` は layering の対象にせず、最外側のルート設定ファイルだけを使用します。

## 設定インポート

別の Configuration を再利用する場合は `[import.<name>]` を1個まで宣言します。import は「Companion だけを取り込む」機能ではなく、Configuration を1段内側へ重ねる仕組みです。Target、Companion、共有パターン、Case 定義は名前解決の対象になり、import 先の `[output]` だけは実行しません。

たとえば次の配置で、`context/dirpluck.toml` から `shikumi/dirpluck.toml` を取り込めます。

```text
projects/
├── shikumi/
│   └── dirpluck.toml
└── context/
    └── dirpluck.toml
```

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"

[output]
path = "context.zip"
if_exists = "overwrite"
```

この Root Configuration 自身に Target や Companion がなくても、import chain の解決後に Target または Companion が残れば有効です。

### `root`

`root` は必須です。**その `[import.<name>]` を記述した Configuration file 自身の所在ディレクトリ**から見た相対ディレクトリとして指定します。`..` は使用できます。絶対 path と glob は使用しません。path separator は `/` を正規形とし、Windows drive path や UNC path を含む絶対指定は OS にかかわらず拒否します。

解決された `root` は直下の import 先 Configuration の execution root / filesystem boundary になります。chain が続く場合、次の import の `root` も同じ規則で、その Configuration file 自身の所在ディレクトリから解決します。

### `configuration`

`configuration` は import root から見た相対 TOML file path です。

```toml
configuration = "shikumi/dirpluck.toml"
```

絶対 path、import root 外へ出る `..`、glob は使用できません。通常の cwd / `./dirpluck/` 探索は行わず、この1 file を直接読み込みます。

### linear chain と循環参照

import 先 Configuration も `[import.<name>]` を最大1個だけ持てます。

```text
A imports B
B imports C
C imports D
```

このような chain の長さは制限しません。解決時には Configuration file の実パスを chain として保持し、現在の chain に既に存在する file が再登場した場合だけ循環参照として拒否します。

```text
A -> B -> C -> A   error
```

エラーでは循環した Configuration chain を示します。深さそのものに warning や上限は設けません。

### 名前解決と shadow

名前解決は最深部から最外側へ行います。

- Target は論理名 `target` の singleton として扱い、外側の Target が内側の Target を base / Case ごと置き換えます。
- Companion は `<name>` ごとに解決し、外側の同名 Companion が内側の定義を path / description / base / Case ごと置き換えます。異なる名前は共存します。
- include 用共有パターンと exclude 用共有パターンは別々の名前空間で `<name>` ごとに解決し、外側の同名定義が内側を置き換えます。
- Selection の `*_pattern_refs` は、この解決後の共有パターン名前空間で評価します。参照を記述した Configuration 内に定義がなくても、chain の外側で最終的に解決できれば有効です。

import 名は link を識別するために使い、0.5.0 の実効名前解決で Companion や共有パターンへ自動 prefix を付ける namespace ではありません。

### import root 内へ Companion を追加する

既存の `[import.<name>.companion.<companion-name>]` は、直下の import root を基準に Companion を追加または override したい場合に使用できます。

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The shikumi project itself."
include_if_exists = ["*"]
if_empty = "allow"
```

この Companion は最終的には通常の Companion 名 `project` として名前解決へ参加します。import 先の `[companion.project]` があればこの定義が外側から shadow します。同じ Configuration で `[companion.project]` と `[import.shikumi.companion.project]` を同時に定義することはできません。

`path` は直下の import root 相対です。`path = "."` で import root 自体を Companion として扱えます。絶対 path、`..`、glob は使用できません。

### Target の解決

実効設定に残った Target がルート設定ファイル自身の定義なら、従来どおり CLI の `DIRECTORY` を1個以上束縛します。

実効設定に残った Target が import chain 内側の Configuration に由来する場合、外側 CLI から `DIRECTORY` は渡しません。その Target の対象ディレクトリは、Target を定義した Configuration file の配置から次の形だけを解決します。

```text
<project>/dirpluck.toml          -> <project>
<project>/dirpluck/<name>.toml   -> <project>
```

import 由来 Target が最終的に残るのに Configuration file がこのどちらの配置にも当てはまらない場合は、対象ディレクトリを一意に決定できないため設定エラーです。外側の Target が shadow する場合、内側 Target の project directory を解決する必要はありません。

### Case

`[import.<name>].case` は使用しません。Configuration chain を名前解決した後、CLI の `--case` を実効設定全体へ1個だけ適用します。Target または Companion が外側で shadow された場合、その source に属する Case 定義も一緒に置き換わります。

## 対象

各 Configuration は `[target]` を最大1個だけ定義できます。Target は `path` を持たず、base 選択と必要な Case 選択を記述します。

```toml
[target]
description = "The submission currently being reviewed."
include = [
    "documents",
    "metadata.json",
]
```

Configuration chain では外側の Target が内側の Target を定義全体として shadow します。したがって実効設定へ残る Target は最大1個です。

ルート設定ファイル自身の Target が残る場合は CLI の `DIRECTORY` が1個以上必須で、同じ Target 選択を各 runtime directory へ適用します。

```console
dirpluck submissions/acme submissions/contoso
```

import 由来 Target が残る場合は CLI `DIRECTORY` を指定せず、その Target を所有する Configuration の project directory を import 節の規則で自動解決します。

```console
dirpluck --config composed-context
```

Target が実効設定に存在しない場合も `DIRECTORY` は指定できません。

Target は既定選択、名前付き Case、またはその両方を持てます。Case だけを持ち `[target]` の既定選択を持たない Target では、実行時に `--case` が必須です。

## コンパニオン

固定 path の source には Companion を使います。

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]
```

Companion 名は Configuration chain 全体での名前解決キーになります。内側と外側に同名 Companion があれば外側の定義が path、description、base、Case を含めて全体を shadow します。異なる名前の Companion はすべて実効設定へ残ります。

通常の `[companion.<name>]` の `path` はその定義を所有する Configuration layer の execution root 相対です。`[import.<name>.companion.<name>]` は直下 import root 相対です。shadow されずに残った Companion は、その定義に対応する execution root を保持したまま実行されます。

Companion だけで実効設定を構成することもできます。この場合は位置引数を指定しません。

## 共有パターン

複数の Selection で同じ include / exclude pattern 集合を使う場合は、名前付き共有パターンを定義します。

```toml
[shared.include_patterns]
project-core = [
    "pyproject.toml",
    "src",
    "README.md",
]

[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
]
```

Selection からは従来どおり名前を明示します。

```toml
[target]
description = "The current project."
include_pattern_refs = ["project-core"]
exclude_pattern_refs = ["python-dev"]
```

Configuration chain では include 用と exclude 用を別々の名前空間として、最深部から最外側へ同名定義を shadow します。0.5.0では import 名を pattern 名へ prefix する必要はありません。

たとえば内側 Configuration が `python-dev` を定義し、外側が同名 `python-dev` を定義すれば、実効設定では外側の定義だけが有効です。内側の Target / Companion が `exclude_pattern_refs = ["python-dev"]` を持っていてその source 自体は shadow されずに残った場合も、参照は最終的な実効 `python-dev` へ解決されます。

逆に、内側 Selection が参照する共有名を内側で定義していなくても、外側の layer で同名が提供されて最終的に一意に解決できれば有効です。chain 全体を解決しても参照先が存在しない場合は設定エラーです。

共有参照と直接記述の `include` / `include_if_exists` / `exclude` は併用できます。参照した共有パターンを展開し、その後に Selection 自身の直接パターンを追加します。実効パターンが重複した場合は設定エラーです。

Case は base Selection を継承しないため、共有パターン参照も継承しません。必要な Case は参照名を自分で記述します。

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

ディレクトリを `include` または `include_if_exists` で選ぶと、その配下は再帰的に収集されます。dirpluck は隠しファイルや秘密情報らしい名前を自動判定しないため、広い選択ではワークスペースに応じた `exclude` を自分で指定してください。上の一覧は例であり、秘密情報を網羅するものではありません。

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

Case は実効設定全体で共有する1個の平坦な名前付き selection variation です。一回の実行で有効にできる Case 名は最大1個で、CLI の `--case` から指定します。

Configuration layer ごとに別の Case を選ぶ仕組みはありません。`[import.<name>].case` は0.5.0では使用しません。

Source が outer layer で shadow された場合、その source の base とすべての Case 定義もまとめて置き換わります。shadow されずに残った source の Case は origin layer に関係なく実効設定の一部として扱います。

対象がある場合、選択した Case 名は `[target.case.<name>]` として存在する必要があります。各 Companion は同名 Case があれば使い、なければ base へフォールバックします。Target がない場合は少なくとも1個の Companion が同名 Case を定義する必要があります。

Case 定義は base の差分ではなく完全な Selection です。base の include / exclude や共有パターン参照を暗黙継承しません。

## 出力

各 Configuration は単独利用できる形式として `[output]` を持ちます。Configuration chain を構成した場合でも出力定義は名前解決の対象にせず、一回の実行で有効になるのは最外側のルート設定ファイル自身の `[output]` だけです。内側 Configuration の `[output]` は schema validation だけを行い、path 解決、collision check、directory 作成、書き込みには使用しません。

有効な出力は、ひとつの既知 path を更新する**固定出力**か、実行ごとに時刻を含む新しい名前を作る**動的命名出力**のどちらかです。2つの形式は混在できません。

### 固定出力

```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`path` はルート設定ファイルの実行 root である cwd 配下の具体的な path です。`if_exists` は必須で、次のどちらかを指定します。

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
dirpluck --config project-snapshot --sequence 3
```

この場合、番号は timestamp の直後に入ります。

```text
project-20260916-011623-3-review.zip
```

`--sequence` は自動採番ではありません。dirpluck は既存ファイルから次の番号を推測せず、指定されなければ番号部分を付けません。固定出力では `--sequence` を指定できません。

動的命名出力では `if_exists` を指定できず、確認時点で生成された名前が既に存在すればエラーです。自動採番や自動リネームは行いません。dirpluck は同じ出力 path への並行書き込みを調停しないため、実行が重なる可能性がある場合は呼び出し側が異なる名前を与える必要があります。

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
dirpluck submissions/acme submissions/contoso
```

監査用 variation:

```console
dirpluck submissions/acme submissions/contoso --case audit
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
dirpluck --config project-snapshot
```

すべての source が固定コンパニオンなので、この設定ファイルは対象なしで完結します。実行ごとに `project-YYYYMMDD-HHMMSS-snapshot.zip` が追加されます。同じ秒にスクリプトから複数生成する場合だけ、呼び出し側が `--sequence N` を明示できます。

## 完全な例: 別の設定ファイルを取り込む

次の root configuration を `workspace/dirpluck/` から実行するとします。

```toml
[target]
description = "The dirpluck project being prepared for development context."
include_if_exists = ["*"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[shared.exclude_patterns]
python-dev = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "*.pyc",
]

[import.shikumi-stack]
root = ".."
configuration = "shikumi/dirpluck.toml"

[import.shikumi-stack.companion.project]
path = "shikumi"
description = "The shikumi project itself, added by the Root Configuration."
include_if_exists = ["pyproject.toml", "src", "README.md"]
exclude_pattern_refs = ["python-dev"]
if_empty = "allow"

[output]
path = "development-context.zip"
if_exists = "overwrite"
```

import 先の `workspace/shikumi/dirpluck.toml` が次のように `shikumi-devdoc` を Companion として宣言していれば、その path は import root である `workspace/` を基準に解決されます。

```toml
[target]
description = "The project selected when this Configuration is run directly."
include_if_exists = ["*"]
if_empty = "allow"

[companion.shikumi]
path = "shikumi"
description = "The shikumi wheel used by related projects."
include = ["dist/shikumi-*.whl"]

[companion.devdoc]
path = "shikumi-devdoc"
description = "The shikumi-devdoc wheel used for document generation."
include = ["dist/shikumi_devdoc-*.whl"]

[output]
path = "shikumi-context.zip"
if_exists = "overwrite"
```

root configuration の実行では import 先の `shikumi-context.zip` は作成も上書きもされません。最終成果物は root configuration の `development-context.zip` だけです。

```console
dirpluck . --dry-run
dirpluck .
```

root configuration の Target は CLI の `.` から決まります。import 先では Target を使用せず、import 先設定由来の `shikumi-stack.shikumi` / `shikumi-stack.devdoc` と、Root 側で追加した `shikumi-stack.project` を Companion として取り込みます。

## 設定探索

既定では `dirpluck.toml` を探索します。`--config NAME` では `.toml` を省略できます。

```console
dirpluck DIRECTORY [DIRECTORY ...] --config review
```

この探索はルート設定ファイルを選ぶときだけ、cwd と `./dirpluck/` の直下で行います。同じ名前が両方に存在する場合は優先順位で解決せず、曖昧としてエラーにします。設定インポートの `root` は選択されたルート設定ファイル自身の所在ディレクトリを基準に解決します。設定インポートは探索を行わず、`configuration` に書かれた import root 内の相対 file path を直接読み込みます。

次のコマンドで検出可能な設定を列挙できます。

```console
dirpluck --configs
```

## 厳密な構文と実行規則

この文書は設定をどう構成して書くかを説明します。`SPECIFICATION.md` は include / exclude の厳密なパターン文法、case-sensitive matching、シンボリックリンク境界、アーカイブ path、dry-run、validation error の最終的な規範です。
