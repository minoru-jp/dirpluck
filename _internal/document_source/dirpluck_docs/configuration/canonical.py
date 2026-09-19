from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}} Configuration Guide")
class TITLE_1:
    r'''この文書は、{{TERM_2}}を TOML で書くためのガイドです。各 field の厳密な validation、pattern grammar、import resolution、filesystem boundary などは `SPECIFICATION.md`、Configuration の選択方法と CLI option は `CLI.md`、Configuration と filesystem 操作の信頼境界は `TRUST.md` を参照してください。'''
    vocabulary_refs @= (terms.TERM_1, terms.TERM_2)

    @title("基本形")
    class TITLE_2:
        r'''Configuration はひとつの最終アーカイブ意図を表します。最小構成では source と output を定義します。

```toml
[companion.notes]
path = "notes"
description = "Notes included in the package."
include = ["*.md"]

[output]
path = "artifacts/notes.zip"
if_exists = "overwrite"
```

実行ごとに変わる source がある場合は{{TERM_3}}、Configuration に path を固定する source は{{TERM_5}}として表します。必要に応じて{{TERM_12}}、{{TERM_4}}、{{TERM_13}}を追加します。'''
        vocabulary_refs @= (terms.TERM_3, terms.TERM_4, terms.TERM_5, terms.TERM_12, terms.TERM_13)

    @title("About")
    class TITLE_202:
        r'''Configuration 全体の目的や、生成される Archive が何をまとめたものかを説明したい場合は `[about]` を使います。`[about]` 自体は任意です。定義する場合は空でない `description` を1つ持ちます。

```toml
[about]
description = "Materials prepared for reviewing the authentication redesign."
```

この description は生成される Archive README の見出し直下に表示され、各 source の `description` より一段上の説明になります。Import chain では外側の Configuration から内側へ探索し、最初に定義された `[about].description` を使います。Chain 全体に定義がなければ README に全体説明は追加しません。正確な resolution は `SPECIFICATION.md` を参照してください。'''

    @title("Path notation")
    class TITLE_201:
        r'''Configuration の filesystem location を表す path は、host OS に関係なく `/` を separator として書きます。Backslash は path separator として使いません。

相対 path は field ごとに定められた基準から解決します。Absolute path は host OS が absolute root として認識する形を `/` separator で記述します。

```text
# POSIX host
/opt/company/references

# Windows host
C:/Users/name/references
//server/share/references
```

Absolute path はその場所を直接参照するため、Configuration の portability は低くなります。別の OS の absolute-root notation への変換、`~` expansion、environment-variable interpolation は行いません。

この規則は Target location `path`、Companion `path`、import `root`、output `path` / `directory` など filesystem location を表す field に適用します。Include pattern、imported `configuration`、CLI Target reference のように意図的に relative と定義される値は、それぞれの制約に従います。厳密な validation は `SPECIFICATION.md` を参照してください。'''

    @title("Target")
    class TITLE_3:
        r'''Target は、実行時に選ぶ source directory へ同じ選択規則を適用するときに使います。

```toml
[target]
description = "The submission currently being reviewed."
include = ["documents", "metadata.json"]
include_if_exists = ["attachments"]
exclude = [".git/", "__pycache__/", "*.pyc"]
```

Target 自体には source path を固定しません。Locating namespace を使わない CLI argument は従来どおり cwd から解決します。

```console
{{TERM_1}} submissions/acme submissions/contoso
```

Configuration workspace と Target の実体を分離したい場合は、Target の下に{{TERM_16}}を定義します。

```toml
[target.location.work]
path = "/srv/work"

[target.location.oss]
path = "../external-projects"
```

Location 名は CLI argument の先頭 segment として使います。

```console
{{TERM_1}} work/acme
{{TERM_1}} oss/example
```

`work/acme` は `work` location の `path` を基準に `acme` を探します。先頭 segment に一致する location がなければ argument 全体を cwd 相対として解決します。Location 名と cwd 上の directory 名が衝突する場合は `./work/acme` のように `./` を付けると location lookup を行わず cwd 相対を明示できます。

Location 直下の directory をすべて Target として使う場合は、location 名だけに末尾 `/` を付けます。

```console
{{TERM_1}} work/
```

これは `work` location 直下の directory をそれぞれ独立した Target として展開します。再帰的には列挙しません。`work/` のような location 展開で指定した名前が定義されていない場合は cwd へ fallback せず error です。

Relative location `path` はその Target definition を所有する Configuration layer の execution root を基準に解決し、absolute `path` は host filesystem 上の場所を直接参照します。Target reference の解決、location boundary、archive path の正確な規則は `SPECIFICATION.md` を参照してください。

Target がない Configuration では positional Target argument は使いません。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_16)

    @title("Companion")
    class TITLE_4:
        r'''Companion は Configuration 側で source directory を固定するときに使います。`path` は relative path と absolute path のどちらでも指定できます。

```toml
[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[companion.company_reference]
path = "/srv/company/reference"
description = "Reference material maintained outside this project."
include = ["*.md"]
```

Relative `path` は、その Companion definition に対応する Configuration execution root を基準に解決します。`..` を使ってその root の外を参照することもできます。Absolute `path` は host filesystem 上の場所を直接参照します。いずれの場合も、解決された Companion source directory 自体が selection の境界となり、include や symbolic link を使ってその外へ抜けることはできません。

複数の Companion は名前を変えて定義します。Companion だけで完結する Configuration も有効です。Archive 内での path の決め方や symbolic link の厳密な扱いは `SPECIFICATION.md` を参照してください。'''

    @title("Selection")
    class TITLE_5:
        r'''Target、Companion、Case はそれぞれ独立した selection を持ちます。selection では `description` と、include 候補を記述します。'''

        @title("`description`")
        class TITLE_6:
            r'''その source が抽出意図の中で果たす役割を書きます。生成される{{TERM_10}}では、この description が archive path の意味を説明するために使われます。Target / Companion のような dirpluck 固有の役割名を索引へ補足しないため、単なる directory 名ではなく、受け取る側だけでも内容を理解できる説明を記述してください。

```toml
description = "Reference material used to evaluate the submission."
```'''
            vocabulary_refs @= (terms.TERM_10,)

        @title("`include`")
        class TITLE_7:
            r'''存在が必要な候補です。

```toml
include = ["report.pdf", "data/*.csv"]
```'''

        @title("`include_if_exists`")
        class TITLE_8:
            r'''存在しないことが正常な候補です。

```toml
include_if_exists = ["generated/*.pdf", "coverage.xml"]
```

`include` と `include_if_exists` は同じ selection で併用できます。'''

        @title("`exclude`")
        class TITLE_9:
            r'''既に include 候補として選んだ範囲から、名前で除外するときに使います。

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

ディレクトリを include すると配下も収集対象になります。Selection には内容や名前に基づく暗黙の除外を加えません。Configuration を実行するときの信頼境界と広い selection の扱いは `TRUST.md` を参照してください。'''

        @title("`if_empty`")
        class TITLE_10:
            r'''任意候補だけの selection で、0 file を正常としたい場合に使います。

```toml
include_if_exists = ["generated/*.pdf"]
if_empty = "allow"
```

既定は `"error"` です。組み合わせ可能な field の厳密な条件は `SPECIFICATION.md` を参照してください。'''

    @title("Shared patterns")
    class TITLE_11:
        r'''同じ include / exclude 配列を複数 selection で使う場合は{{TERM_12}}として名前を付けます。

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

Import を使う場合の shared pattern name resolution は `SPECIFICATION.md` で定義します。'''
        vocabulary_refs @= (terms.TERM_12,)

    @title("Cases")
    class TITLE_12:
        r'''{{TERM_4}}は、同じ source に別の完全な selection を用意するときに使います。

```toml
[target]
description = "Normal review."
include = ["documents", "metadata.json"]

[target.case.audit]
description = "Audit review."
include = ["documents", "metadata.json", "records"]
```

```console
{{TERM_1}} submissions/acme --case audit
```

Case は base selection への差分ではありません。Case で必要な include / exclude / shared pattern reference は Case 自身へ書きます。

Target と Companion が同じ Case 名を持てば、同じ CLI `--case` で対応する variation を選べます。Companion に同名 Case がない場合の扱いなど、正確な Case semantics は `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_4)

    @title("Configuration import")
    class TITLE_13:
        r'''既存の Configuration を内側の layer として再利用するときは{{TERM_13}}を使います。

```toml
[import.shikumi]
root = ".."
configuration = "shikumi/dirpluck.toml"
```

`root` は relative path と absolute path のどちらでも指定できます。Relative `root` はこの import を書いた Configuration file の所在 directory を基準に解決し、absolute `root` は host filesystem 上の場所を直接参照します。`configuration` は解決した import root 内の relative TOML file path のままです。

Import された definition と現在の Configuration の definition から{{TERM_15}}が構成されます。同名 definition がある場合の shadowing、chain、cycle、shared pattern resolution の正確な規則は `SPECIFICATION.md` にまとめています。

Import 先の Target が{{TERM_15}}へ残る場合でも、実際の Target directory は CLI positional `TARGET` から選びます。Target location を持つ imported Target では、その location も Target definition の一部として残ります。Import 先 Configuration file の directory を runtime Target として推論しません。

Import root 内の固定 source を親側から Companion として追加したい場合は overlay を使えます。

```toml
[import.shikumi.companion.project]
path = "shikumi"
description = "The imported project itself."
include_if_exists = ["pyproject.toml", "src", "README.md"]
if_empty = "allow"
```'''
        vocabulary_refs @= (terms.TERM_13, terms.TERM_15)

    @title("Output")
    class TITLE_14:
        r'''各 Configuration は `[output]` を持ちます。固定 path を更新する形式と、timestamp 付きの名前を作る形式があります。'''

        @title("Fixed output")
        class TITLE_15:
            r'''```toml
[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

`path` は cwd 基準の relative path または absolute path を指定できます。`if_exists` は `"error"` または `"overwrite"` です。ひとつの既知 artifact を更新する用途に向きます。'''

        @title("Generated output")
        class TITLE_16:
            r'''```toml
[output]
directory = "artifacts/snapshots"
prefix = "project"
timestamp = true
suffix = "snapshot"
```

`directory` は cwd 基準の relative path または absolute path を指定できます。定例 snapshot のように run ごとに artifact を蓄積する用途に向きます。同じ秒に複数 run を意図的に開始する場合は CLI `--sequence N` を使えます。

Filename layout、collision、concurrent write、inner Configuration の output の扱いは `SPECIFICATION.md` を参照してください。'''

    @title("Complete example")
    class TITLE_17:
        r'''```toml
[about]
description = "Materials prepared for reviewing the current project."

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

[target.location.projects]
path = "/srv/projects"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
{{TERM_1}} projects/example
{{TERM_1}} projects/example --case full --dry-run
{{TERM_1}} projects/
```

CLI の全 option と Configuration discovery は `CLI.md`、この Configuration が正確にどう解決・検証されるかは `SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)
