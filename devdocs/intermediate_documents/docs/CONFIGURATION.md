<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_11",
      "text": "pluck"
    },
    {
      "source": "canonical_documents.vocabulary.canonical",
      "identifier": "TERM_19",
      "text": "Invocation Template"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `devdocs/canonical_documents/configuration/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/intermediate_documents/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck Configuration Guide

この文書は、設定ファイルを TOML で書くためのガイドです。各 field の厳密な validation、base composition、pattern grammar、filesystem boundary、output collision などは `SPECIFICATION.md`、Configuration の選択方法と CLI option は `CLI.md`、Configuration と filesystem 操作の信頼境界は `TRUST.md` を参照してください。

## Configuration document

Configuration は `.dirpluck` extension を持つ document として保存し、内容には TOML syntax を使用します。`.toml` extension は dirpluck Configuration として受理しません。

```text
default.dirpluck
review.dirpluck
configs/common.dirpluck
```

`default.dirpluck` は CLI で `--config` を省略したときだけ、runtime cwd から自動的に使用される特別な filename です。別名 Configuration や別 directory の Configuration は `--config PATH` で明示的に選びます。Relative CLI path は cwd 基準、Configuration 内の relative filesystem path はその Configuration file の directory 基準です。Configuration document を選択・参照する path は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path も利用できます。Relative path の基準には link target の実体 location ではなく、選択・参照した document path の directory を使います。詳しい選択規則は `CLI.md` / `SPECIFICATION.md` を参照してください。Base Configuration は filename に特別な default name を必要とせず、`[about].base` から concrete `.dirpluck` path を参照します。

`.dirpluck-inv` は Configuration ではなく、CLI invocation を保存する別 document type です。Configuration の schema や base chain には参加しません。Invocation Template の書き方と選択方法は `CLI.md` を参照してください。

## 基本形

Configuration はひとつの最終 Archive intent を表します。実行時に選ぶ Target がある場合は `pluck` と `scope`、Configuration に固定する source は `always` で表します。

```toml
[pluck]
description = "The project currently under review."
may = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]
allow_empty = true

[scope]
ignore = ["archive", "tmp-*"]

[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[output]
path = "artifacts/review.zip"
```

`[pluck]` は対象へ適用するpluck、`[scope]` / `[scope.<name>]` は Target を探すスコープ、`[always.<name>]` は常時ソースです。Archive 上で同名の source root を区別する必要がある場合はネームスペースを使えます。必要に応じて共有パターン、ケース、基底設定ファイルを使って構成を広げます。

## About

`[about]` は Configuration 自身についての宣言です。`description` と `base` を持てます。

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
base = "../common/common.dirpluck"
```

`description` は任意で、生成される Archive README の見出し直下に表示する Configuration 全体の説明です。Base chain に複数の description がある場合は、外側から見て最初に定義されたものを使います。

`base` も任意で、この Configuration が基礎とする基底設定ファイルを1個指定します。`description` を書かず `base` だけを書くこともできます。`[about]` を定義する場合は、少なくともどちらか一方を記述します。

Base chain の composition と cycle detection は `SPECIFICATION.md` を参照してください。

## Path notation

Configuration で filesystem location を表す path は、host OS に関係なく `/` を separator として書きます。Backslash は path separator として使いません。Windows でも `C:/...` や `//server/share/...` のように `/` を使います。

相対 filesystem path は、**その field が記述されている Configuration file の directory**を基準に解決します。Runtime cwd を path resolution base として切り替えることはありません。

```text
project/default.dirpluck
    [always.notes]
    path = "../notes"
        -> project/ から解決
```

Absolute path は host OS が absolute root として認識する形を `/` separator で記述します。

```text
# POSIX host
/opt/company/references

# Windows host
C:/Users/name/references
//server/share/references
```

Absolute path はその場所を直接参照するため、Configuration の portability は低くなります。別 OS の absolute-root notation への変換、`~` expansion、environment-variable interpolation は行いません。

この基準は少なくとも `about.base`、`scope.<name>.path`、`always.<name>.path`、`output.path`、`output.timestamp.path` に共通です。Configuration document 自体を参照する `about.base` だけでなく、named Scope / Always のように明示した source root location も host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む location を利用できます。明示 root の alias を解決して source root とすることと、その root からの自動 traversal で link-like entry を選択しないことは別です。Pattern や CLI Target reference のように filesystem location ではない値は、それぞれの規則に従います。厳密な validation は `SPECIFICATION.md` を参照してください。

## Pluck

`[pluck]` は、今回の実行で選ばれた対象から何を取り出すかを定義します。Source path 自体は持たず、Target はスコープと CLI Target reference から解決します。

```toml
[pluck]
description = "The submission currently being reviewed."
must = ["documents", "metadata.json"]
may = ["attachments"]
ignore = [".git/", "__pycache__/", "*.pyc"]
```

同じ実行で複数 Target を選んだ場合も、各 Target へ同じ pluck selection を独立して適用します。

Pluck がない Configuration では positional Target reference を使いません。

## Scope

スコープは Target を探す場所です。常設の default Scope と、必要に応じて追加する名前付き Scope を使えます。

Default Scope は常に存在し、ルート設定ファイルがある directory を探索 root とします。`[scope]` table は default Scope の optional `ignore` / `namespace` を設定するために使い、`path` は書きません。`[scope]` を省略した場合、または空の `[scope]` を書いた場合は `ignore = []`、Namespace なしと同じです。Base Configuration に書いた `[scope]` は、その Configuration 自身を Root として使う場合だけ有効で、outer Root の default Scope へ継承されません。

```toml
[scope]
ignore = ["archive", "tmp-*"]
```

名前付き Scope は `path` を持ちます。

```toml
[scope.work]
path = "../work"
ignore = ["archive", "tmp-*"]

[scope.oss]
path = "/srv/oss"
ignore = ["old-*"]
```

`ignore` は Scope 直下で Target candidate として扱わない directory name を指定します。File selection の `pluck.ignore` とは役割が違います。

CLI Target reference は Scope の有無と、1 Target / 全 Target の組み合わせとして次の4形です。

```text
NAME        -> 無名 Scope から1 Target
SCOPE/NAME  -> 名前付き Scope から1 Target
/           -> 無名 Scope の全 Target
SCOPE/      -> 名前付き Scope の全 Target
```

全展開は Scope 直下の eligible directory だけを対象とし、再帰しません。

Base chain では名前付き Scope だけを名前ごとに重ね、同名 Scope は外側の Configuration が置き換え、異名 Scope は共存します。Default Scope は base から継承せず、常に root Configuration に属します。したがって Base の `[scope].ignore` / `namespace` は outer Root では使用されませんが、その Base Configuration 自身を Root として使う場合には通常どおり有効です。名前付き Scope の root は定義元 Configuration を基準にした場所のままで rebase しません。

Scope には任意で `namespace = "<name>"` を指定できます。これは Target の探索場所を変えず、その Scope から得た Target の Archive root に、別途定義したネームスペースを prefix として追加します。Namespace は衝突時だけ自動適用されるものではなく、指定した Scope の Target に常に適用されます。

名前付き Scope の path が現在の filesystem で利用可能かどうかは、その Scope を Target reference で実際に使うときに確認します。未マウントなどで存在しない named Scope が定義されていても、別の Scope だけを使う実行は妨げません。Named Scope の root location 自体は symbolic link / Windows directory junction を含められますが、解決した Scope root 直下で自動発見した link-like entry は Target として選択・展開しません。厳密な duplicate root、Namespace reference、Target resolution の規則は `SPECIFICATION.md` を参照してください。

## Namespace

ネームスペースは、source root が Archive 上で同じ path に解決される場合などに、source を明示的に区別して配置するための Archive 専用 prefix です。Namespace 自体は名前付きの空 table として定義します。

```toml
[namespace.work]

[namespace.external]
```

Namespace 名そのものが Archive 上の1 directory 名になります。現時点で `[namespace.<name>]` は属性を持ちません。不要な設定値を持たせず、将来 Namespace 固有の policy が必要になった場合に同じ table を拡張できる構造とします。

Scope と Always source は Namespace 名を参照できます。

```toml
[namespace.work]
[namespace.external]

[scope.work]
path = "/srv/work"
namespace = "work"

[always.docs]
path = "../docs"
namespace = "external"
description = "External documentation."
must = ["*.md"]
```

たとえば `work/project` の source root が `project/` なら `work/project/`、Always source の通常の source root が `docs/` なら `external/docs/` として Archive に配置します。Namespace を指定しない source は従来どおり source root 自体を Archive root とします。

異なる resolved source の最終 Archive root が同じになる場合、dirpluck は source を黙って merge せず error にします。Namespace はこの衝突を明示的に避けるために使えますが、自動的に一意性を保証するものではありません。同じ Namespace を共有して最終 Archive root が再び同じになれば error です。

生成されるアーカイブREADMEは、Namespace を使う run では Namespace が Archive 専用の外側 directory であることを説明します。各 source は final Archive root 自体を見出しとして表示し、Namespace を使う source では Namespace と Source root も metadata として分けて示します。これにより受け手は Namespace directory を元 filesystem path の一部と誤認せず、その直下が source root であることを確認できます。

## Always

`[always.<name>]` は Configuration 側で source directory を固定し、実行のたびに参加させる常時ソースです。`path` は relative path と absolute path のどちらでも指定できます。

```toml
[always.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
must = ["*.md"]

[always.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
must = ["*.md"]
```

Relative `path` は、その definition が記述されている Configuration file の directory を基準に解決します。`..` を使って外側の directory を参照することもできます。Absolute `path` は host filesystem 上の場所を直接参照します。明示した Always root location は symbolic link / Windows directory junction を含めることができ、alias の参照先 directory を source root として利用します。Archive 上の source root 名は実体側へ置き換えず、Configuration に書いた location 側の name / relative path を使います。

解決された source directory 自体が selection boundary です。Root 自体に alias を使えることと、Source 内の自動 traversal で link-like entry をたどることは別です。Source 内で symbolic link または Windows directory junction として認識した entry は選択せず、リンク先もたどりません。

Always source には任意で `namespace = "<name>"` を指定し、定義済みのネームスペースを Archive root の外側へ追加できます。Filesystem 上の source path や selection boundary は変わりません。

Always source の Selection は Target の Pluck とは独立して評価します。同じ physical file が Target 配下にも存在していても、Target 側の `ignore` や Selection result は Always source の Selection を変更しません。両方が同じ physical file を選択し、異なる Archive path に配置する場合は両方を収録します。生成されるアーカイブREADMEでは、Always source が実際に選択した file と Target が実際に選択した file に physical overlap がある場合、その Always source section に Target 側の Archive root と重複 file 数を表示します。

複数の Always source は名前を変えて定義します。Pluck を持たず Always source だけで完結する Configuration も有効です。

## Selection

Pluck、Always source、Case はそれぞれ独立した選択を持ちます。Selection では `must` / `may` / `ignore`、必要に応じて `allow_empty` を記述し、人間向けの説明を添えたい場合だけ `description` を使います。

### `description`

その source が抽出意図の中で果たす役割を書きます。生成されるアーカイブREADMEでは、この description が archive path の意味を説明するために使われます。

```toml
description = "Reference material used to evaluate the submission."
```

`description` は任意です。省略しても selection の抽出意味論は変わりません。記述する場合は空でない string とし、生成される Archive README ではその source の見出しと file 数に続く本文として使われます。複数行の説明も table cell へ圧縮せず、そのまま section body として表示します。

### `must`

存在を要求し、存在するものを selection に含める candidate です。

```toml
must = ["report.pdf", "data/*.csv"]
```

Pattern が1件も一致しなければ selection は成立しません。

### `may`

存在する場合だけ selection に含め、不在を error にしない candidate です。

```toml
may = ["generated/*.pdf", "coverage.xml"]
```

`must` と `may` は同じ selection で併用できます。

### `ignore`

既に `must` / `may` から選択候補になった範囲で、pluck しない entry を指定します。通常の string は従来どおり file / directory **name** を照合します。

```toml
ignore = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".env*",
    "*.pem",
    "*.key",
    "*.pyc",
]
```

特定の場所だけを除外したい場合は、1要素 nested array の中を `./` で始めて Selection root からの concrete relative path を指定できます。

```toml
ignore = [
    ["./tests/fixtures/big.bin"],
    ["./src/generated/"],
]
```

Pluck では `./` は現在の Target root、Always source ではその Always source root を表します。末尾 `/` は directory path、末尾 `/` なしは file path として扱い、filesystem の現在状態から種類を推測しません。Path reference は Selection root の内側に限定し、`..`、absolute path、glob、backslash を受理しません。

Name pattern、Shared ignore reference、path reference はすべて除外条件の和として扱います。同じ entry に複数の条件が一致しても error にはなりません。Directory ignore または directory path reference に一致した directory はその時点で除外し、内部を走査しません。評価順序は意味論に含めません。

`ignore` は entry の種類による診断より優先し、一致した entry は selection 対象から外した時点で処理済みとします。そのため ignored entry は symbolic link / Windows directory junction や特殊 filesystem entry であっても、その種類を理由とする runtime diagnostic の根拠にしません。`must` が ignored entry にしか一致しない場合は通常の unsatisfied `must` として扱います。

認識した非 ignored symbolic link / Windows directory junction は `must` / `may` の選択対象にも再帰走査の対象にもならず、Archive へも含めません。FIFO、socket、device など regular file / regular directory ではない非 ignored filesystem entry も Archive 対象にしません。`must` がそのような特殊 entry だけに一致した場合は selectable でない理由を示す error とし、`may` では optional missing として扱います。Selection には内容や名前に基づく暗黙の ignore を加えません。Configuration を実行するときの trust boundary と広い selection の扱いは `TRUST.md` を参照してください。

### `allow_empty`

`may` だけの selection で、最終的に0 file でも正常としたい場合に使います。

```toml
may = ["generated/*.pdf"]
allow_empty = true
```

既定は `false` です。`allow_empty = true` と `must` は同時に使えません。

## Shared patterns

同じ pattern set を複数 selection で使う場合は共有パターンとして名前を付けます。Selection と同じ `must` / `may` / `ignore` の3 namespace を使います。

```toml
[shared.must]
project = ["src", "pyproject.toml"]

[shared.may]
docs = ["README.md", "docs"]

[shared.ignore]
python-noise = ["__pycache__/", "*.pyc"]
```

Selection array の通常の string は direct pattern です。`must` / `may` の1要素 nested array は Shared reference、`ignore` の1要素 nested arrayは plain name なら Shared reference、`./` で始まる string なら Selection-relative path reference として解釈します。

```toml
[pluck]
description = "The current project."
must = [
    "LICENSE",
    ["project"],
]
may = [
    ["docs"],
]
ignore = [
    ".git/",
    ["python-noise"],
]
```

参照先 namespace は、その reference を書いた field から決まります。`must = [["project"]]` は `shared.must.project`、`may` は `shared.may`、`ignore = [["python-noise"]]` は `shared.ignore.python-noise` を参照します。`ignore = [["./tests/fixtures/"]]` のように `./` で始めた場合だけ Shared namespace ではなく Selection-relative path を表します。

`[]`、`["a", "b"]`、`[123]` のような nested array は reference として無効です。`must` / `may` では nested array は Shared reference 専用です。`ignore` では `./` を path reference marker に予約しますが、通常の direct string pattern の表現は変えません。

Base chain での name resolution と duplicate validation は `SPECIFICATION.md` を参照してください。

## Cases

ケースは、同じ source に別の完全な selection を用意するときに使います。

```toml
[pluck]
description = "Normal review."
must = ["documents", "metadata.json"]

[pluck.case.audit]
description = "Audit review."
must = ["documents", "metadata.json", "records"]
```

```console
dirpluck acme --case audit
```

Case は base selection への差分ではありません。必要な `must` / `may` / `ignore` / Shared reference / `allow_empty` は Case 自身へ書きます。

Pluck と Always source が同じ Case 名を持てば、同じ CLI `--case` で対応する variation を選べます。Always source に同名 Case がない場合の fallback など、正確な Case semantics は `SPECIFICATION.md` を参照してください。

## Base Configuration

既存の Configuration を基礎として再利用するときは、`[about]` の `base` で基底設定ファイルを参照します。

```toml
[about]
base = "../common/common.dirpluck"
```

`base` は1個の Configuration file を参照します。参照先がさらに `base` を持つ場合は linear base chain になります。Base chain の深さに固定上限はありません。

各 Configuration に書かれた relative filesystem path は、常にその Configuration file 自身の directory を基準に解決します。Base Configuration から継承した named Scope や Always source の path を、外側 Configuration の位置へ rebase しません。Default Scope も同じ Configuration-directory model に従い、Root Configuration file の directory をそのまま root とします。

Pluck、Always、Scope、Shared pattern の composition、description resolution、cycle detection、Output の扱いは `SPECIFICATION.md` に定義します。Base Configuration は Output を省略できます。Output を持たない root Configuration も `--preview` に使用でき、通常 build でも CLI `--here` / `--output` または Python API `output=` で runtime Output を与えれば実行できます。Runtime Output を使わない build では root 自身の fixed または timestamp Output を直接宣言します。

## Output

出力定義は optional です。共通 definition を提供する Base Configurationだけでなく、`--preview` や runtime Output を使う root Configuration でも Output を省略できます。Runtime Output を指定しない通常 build では、root Configuration 自身に fixed mode または timestamp mode のどちらか一方を直接宣言します。Base の Output は継承されません。

### Fixed output

```toml
[output]
path = "artifacts/review.zip"
overwrite = false
```

`path` は filename まで含む具体的な output file path です。Relative path はこの `[output]` を記述した Configuration file の directory を基準に解決します。

`overwrite` は existing output を置き換えてよいかを表し、既定は `false` です。Output file は毎回通常の新規 file creation と同じ permission semantics で作られ、POSIX では process `umask` が適用されます。`overwrite = true` でも置き換える前の file mode は継承しません。`prefix` / `suffix` は fixed mode では使いません。

### Timestamp output

```toml
[output.timestamp]
path = "artifacts/snapshots/"
prefix = "project"
suffix = "review"
```

`path` は output directory を指定し、末尾 `/` で directory path であることを表します。Relative path はこの definition を記述した Configuration file の directory を基準に解決します。

Filename は次の形で生成します。

```text
[prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
```

`prefix` と `suffix` は timestamp mode 専用です。同じ秒に複数 run を意図的に区別したい場合は CLI `--sequence N` を使えます。CLI `--here` や末尾 `/` の `--output PATH`、Python API の末尾 `/` の `output=` で runtime directory Output を指定した場合も、root Configuration が `[output.timestamp]` を持てば `prefix` / `suffix` は automatic filename の naming rule として再利用されます。Configured `path` は runtime destination には使いません。ZIP entry 自体の mtime を統一する policy は Configuration field ではなく、CLI / Invocation Template の `--archive-mtime` / `archive_mtime` で指定します。

### Writable destination

Output は、Configuration だけから書き込み境界を静的に確定できる形に限定します。Fixed output では指定した完全 file path、timestamp output では指定した directory tree が書き込み境界です。

Base chain 上の Output definitions は互いの書き込み境界へ介入できません。Fixed / timestamp の組み合わせごとの overlap 判定は `SPECIFICATION.md` を参照してください。

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

CLI の全 option と Configuration / Invocation Template の選択方法は `CLI.md`、この Configuration が正確にどう解決・検証されるかは `SPECIFICATION.md` を参照してください。
