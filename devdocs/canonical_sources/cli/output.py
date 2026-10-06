from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_011 = test_target_field("example 011")
example_012 = test_target_field("example 012")
example_013 = test_target_field("example 013")
example_014 = test_target_field("example 014")
example_015 = test_target_field("example 015")
example_016 = test_target_field("example 016")


@summary("Preview、Archive README path、runtime Output、sequence、entry mtime。")
@canonical_source(
    "Preview and runtime output",
    filename="output.md",
    order=30,
    merge_policy="local",
    heading="title",
)
class CLI_PART:
    r"""この文書は preview、Archive README への source path 記録、runtime Output、sequence、Archive entry mtime を説明します。

    Configuration 側の Output authoring は `../configuration/output.md`、厳密な Output semantics は `../specification/output.md`、preview の side-effect boundary は `../specification/preview.md`、Archive planning は `../specification/archive.md` を参照してください。外部へ渡す Archive では `../TRUST.md` も確認してください。"""

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_10

    class SECTION_006:
        r"""
        `--preview` は Archive file を作らず、解決した ZIP contents を tree として表示します。

        ```console
        {{example_011}}
        ```

        Configuration や workspace を変更した後、実際に Archive を書き込む前の確認に使えます。同じ Configuration / Target / Case / Selection 入力なら、preview が示す source selection と Archive 内配置は通常 build の結果と一致します。`--preview` は root Configuration に Output declaration がなくても使用でき、Output destination を解決・書き込みしないため、`--here` / `--output` / `--force` / `--sequence` とは組み合わせません。

        Selection traversal で non-ignored symbolic link / Windows directory junction として認識した entry を除外した場合は、除外件数を informational note として表示します。個々の path は列挙しません。正確な preview semantics と link-like entry の扱いは `specification/INDEX.md` / `TRUST.md` を参照してください。
        """

        title @= "Preview"

        example_011 @= "dirpluck ./acme/ --preview"

        merge @= TERMS.TERM_1

    class SECTION_076:
        r"""
        0.14.0 から 1.0.0 未満では、Selection の旧1要素 nested-array reference は互換入力として受理されますが非推奨です。CLI が実行時に読み込んだ Configuration file で旧記法を検出すると、その file につき1回だけ stderr へ warning を表示します。Base chain で読み込まれた Configuration も対象です。

        Warning は 1.0.0 で旧記法が削除されることを示し、Shared reference は `{ shared = "..." }`、`ignore` の concrete relative path は `{ path = "..." }` へ移行するよう案内します。この migration warning は stdout の archive path / preview tree を変えず、exit status も変更しません。
        """

        title @= "Configuration migration warning"

        merge @= TERMS.TERM_1

    class SECTION_077:
        r"""
        0.16.0 から 1.0.0 直前まで、CLI は Always migration を public warning として stderr へ表示します。0.14.x で有効だった Always source の旧 Archive identity と 0.16.x の effective Always name を比較し、実際に Archive root が変わる source だけに layout migration warning を出します。Warning には旧 root と新 root を含めます。`[always.docs] path = "docs"` のように旧・新 identity が同じ場合、この layout warning は出ません。0.17.0 以降で explicit Layout が有効な Always source では、現在の final Archive destination と食い違う旧 0.16.x placement を表示しないため、この layout migration warning を抑制します。

        Always source に `namespace` がある場合は、layout 差分とは別に pre-1.0 compatibility warning を必ず報告します。0.16.x 以降の 0.x series では Namespace name が Always name を置き換えて Archive placement に使われますが、この field は 1.0.0 で削除されます。Archive directory name は `[always.<name>]` に直接記述してください。

        CLI が表示するこれらの warning は、公式 Python API が `AlwaysMigrationWarning` として報告するものと同じ診断です。CLI は Python warning を重ねて発行せず、収集した message を `dirpluck: warning:` として stderr へ表示します。Warning は stdout の Archive path / preview tree と exit status を変更しません。
        """

        title @= "0.16 Always migration warning"

        merge @= TERMS.TERM_1

    class SECTION_065:
        r"""
        生成される{{TERM_10}}は Archive contents の人間向け index です。参加する Always source と有効化された Extra source はすべて Target より先に並び、各 fixed-source section では任意の `description` を先に示してから selected file 数などの metadata を続けます。Target は Scope ごとにまとめ、directory Target はその Scope の Pluck group 配下に final Archive path を並べます。同じ Scope / Pluck の `description` は Target ごとに繰り返さず、その group に1回だけ表示します。File Target は Pluck を使わないため Scope 直下に表示します。

        README 冒頭の `Scope: "..."` の説明は、Scope 名が Target を探した選択範囲の識別子にすぎず、Target 間の優先度・重要度・階層関係を表さないことを明示します。Scope 名に追加の意味を持たせる場合は `scope.description` に記述します。選択した Case 名、Configuration path / table、base chain などの実行 provenance は記録しません。

        Source filesystem path も各 source section へ含めたい場合だけ `--paths` を指定します。

        ```console
        {{example_012}}
        ```

        `--paths` は各 source section に解決済み source filesystem path を追加します。Directory source では directory path、file Target では file path を表示します。Absolute path を含む local filesystem 情報を Archive に残し得るため、外部へ配布する Archive では必要性を確認して使用してください。
        """

        title @= "Archive index の source path"

        example_012 @= "dirpluck ./acme/ --paths"

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_10

    class SECTION_068:
        r"""
        通常 build の Output destination は CLI から一時的に指定できます。Runtime Output を指定した場合、Configuration の fixed output path / timestamp output directory は書き出し先として使用しません。

        現在の cwd へ書き出す場合は `--here` を使います。

        ```console
        {{example_013}}
        ```

        `--here` だけなら cwd に automatic timestamp filename を生成します。明示 filename は `--here=FILENAME` の形で `=` に続けて指定し、directory component は受理しません。Path を指定する場合は `--output` を使います。`-h` は `--help` の short option として保持し、`--here` に short option はありません。

        任意の runtime path へ書き出す場合は `-o PATH` / `--output PATH` を使います。

        ```console
        {{example_014}}
        ```

        末尾 `/` がない `PATH` は exact output file path、末尾 `/` がある `PATH` は output directory です。Directory form では automatic timestamp filename をその directory 直下へ生成します。Filesystem の既存状態から file / directory を推測せず、directory marker は OS にかかわらず `/` です。Relative `PATH` は runtime cwd を基準にします。Backslash は path separator として受理しません。

        Automatic filename を生成するとき、root Configuration が `[output.timestamp]` を宣言していれば、その `prefix` / `suffix` を naming rule として再利用します。Configured output directory 自体は使いません。Root に timestamp Output がなければ既定名は `dirpluck-YYYYMMDD-HHMMSS.zip` です。`--sequence N` はこの automatic filename にも使用できます。Exact filename を指定した runtime Output では `--sequence` を使えません。

        Runtime Output の overwrite は既定で無効です。Existing destination を置き換える場合だけ `-f` / `--force` を指定します。`--force` は Configuration の fixed / timestamp Output を使う通常 buildにも適用できます。Automatic filename が既存 destination と衝突しても、自動採番・rename・timestamp の取り直しは行いません。

        `--here` と `--output` は同時に指定できません。Output declaration を持たない root Configuration でも、runtime Output を指定すれば通常 build を実行できます。
        """

        title @= "Runtime Output"

        example_013 @= """
        dirpluck ./acme/ --here
        dirpluck ./acme/ --here=context.zip
        """

        example_014 @= """
        dirpluck ./acme/ -o artifacts/context.zip
        dirpluck ./acme/ -o artifacts/snapshots/
        """

        merge @= TERMS.TERM_1

    class SECTION_007:
        r"""
        Automatic timestamp filename を使う Output で、同じ秒に複数 run を意図的に区別したい場合は正の整数 `--sequence N` を指定できます。

        ```console
        {{example_015}}
        ```

        `--sequence` は自動採番ではありません。Configuration の fixed output、`--here=FILENAME`、末尾 `/` を持たない `--output PATH` では使えません。Filename の正確な配置と collision rules は `specification/INDEX.md` を参照してください。
        """

        title @= "Timestamp output の sequence"

        example_015 @= "dirpluck --config project-snapshot --sequence 2"

        merge @= TERMS.TERM_1

    class SECTION_075:
        r"""
        `--archive-mtime VALUE` は、生成する ZIP のすべての entry に1個の共通 timestamp を設定します。Configuration の `[output]` / `[output.timestamp]` には保存せず、CLI または Invocation Template の runtime policy として指定します。

        ```console
        {{example_016}}
        ```

        `VALUE` は次のいずれかです。

        - `YYYY-MM-DDTHH:MM:SS`: timezone を持たない ZIP timestamp literal。1980-01-01T00:00:00 から 2107-12-31T23:59:59 の範囲。
        - `now`: 1 run で local current time を1回だけ取得し、全 entry に同じ値を使う。
        - `zip-epoch`: ZIP の最小 timestamp `1980-01-01T00:00:00` を使う。

        ZIP の timestamp は2秒粒度なので、奇数秒は直前の偶数秒へ切り下げます。指定した値は生成 `README.md`、empty directory entry、source file のすべてに適用します。Option を省略した場合は従来どおり、source file は filesystem mtime、Dirpluck が生成する entry は生成時刻を使用します。

        `zip-epoch` や固定 timestamp は entry timestamp による byte 差を取り除き、reproducible な Archive を作る一助になります。ただし source file の permission bits などの filesystem metadata も ZIP byte 列へ影響し得ます。Dirpluck は permission bits を正規化せず、compressor / runtime を含め Archive 全体の reproducibility をこの option だけで保証しません。`--archive-mtime` は timestamp output の filename に使う `YYYYMMDD-HHMMSS` を変更しません。`--preview` と併用できますが、Archive を書かないため preview result には影響しません。

        Invocation Template では `archive_mtime = "zip-epoch"` のように保存できます。CLI で `--archive-mtime` を指定した場合は、選択した Invocation の値より CLI を優先します。
        """

        title @= "Archive entry の mtime"

        example_016 @= """
        dirpluck ./example/ --archive-mtime 2026-01-01T00:00:00
        dirpluck -i release --archive-mtime zip-epoch
        dirpluck ./example/ --archive-mtime now
        """

        merge @= TERMS.TERM_1
