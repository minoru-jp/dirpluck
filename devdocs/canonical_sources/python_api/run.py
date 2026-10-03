from shikumi_devdoc.fields.api_reference import OPERATION, input, kind, name, output
from shikumi_devdoc.fields.lifecycle import introduced
from shikumi_devdoc.norms.common import canonical_source, summary
from shikumi_devdoc.norms.document import test_target_field, title


run_signature = test_target_field("run signature")
argument_mapping = test_target_field("CLI argument mapping")
exact_output_example = test_target_field("exact runtime output example")
directory_output_example = test_target_field("directory runtime output example")
invocation_example = test_target_field("Invocation Template example")
invocation_cli_example = test_target_field("Invocation Template CLI equivalent")
archive_mtime_example = test_target_field("archive mtime example")


@summary('high-level `run()` entry point と runtime modifier の契約。')
@canonical_source('dirpluck.run', filename='run.md', order=10, merge_policy="local", heading="title")
class API_REFERENCE_PART:
    r"""
    公式 high-level entry point は次の形です。

    ```python
    {{run_signature}}
    ```

    各 argument は CLI の次の入力に対応します。

    ```text
    {{argument_mapping}}
    ```

    `invocation` を使う場合は positional `targets` と `config` を同時に指定しません。`entry` は `invocation` と一緒にだけ使用します。`preview=True` は Output を解決・書き込みしないため `sequence`、`output`、`force=True` とは組み合わせません。`sequence` は 1 以上の integer とします。`output` は CLI `--output` と同じ `/` separator の path syntax を使い、relative path は `cwd` を基準にします。`force` は boolean です。

    Invocation Template を選択した場合、`case` argument は保存された Case、`archive_mtime` argument は保存された `archive_mtime` を CLI と同じ規則で上書きします。Invocation の `config` が未指定なら `cwd/default.dirpluck`、`targets` が未指定なら Target なし、`case` が未指定なら通常の default Case semantics、`archive_mtime` が未指定なら従来の entry timestamp semantics を使います。
    """

    run_signature @= """
    run(
        *targets,
        config=None,
        case=None,
        sequence=None,
        invocation=None,
        entry=None,
        preview=False,
        paths=False,
        archive_mtime=None,
        output=None,
        force=False,
        cwd=None,
    )
    """
    argument_mapping @= """
    targets       positional TARGET
    config        --config PATH
    case          --case NAME
    sequence      --sequence N
    invocation    -i / --invocation-template PATH
    entry         -e / --entry NAME
    preview       --preview
    paths         --paths
    archive_mtime --archive-mtime VALUE
    output        --output PATH
    force         --force
    cwd           Python API only: relative control-document path の runtime anchor
    """

    name @= "dirpluck.run"
    kind @= OPERATION
    introduced @= "0.9.0"
    input @= "targets: positional Target references"
    input @= "config: Configuration document path"
    input @= "case: Case name"
    input @= "sequence: explicit output sequence"
    input @= "invocation: Invocation Template path"
    input @= "entry: named Invocation entry"
    input @= "preview: preview mode"
    input @= "paths: include source paths in generated README"
    input @= "archive_mtime: Archive entry timestamp policy"
    input @= "output: runtime Output path"
    input @= "force: overwrite effective Output"
    input @= "cwd: runtime anchor for relative control-document paths"
    output @= "RunResult"

    class SECTION_035:
        r"""
        0.14.0 から 1.0.0 未満で、読み込んだ Configuration が deprecated な1要素 nested-array reference を使用している場合、`dirpluck.run()` は Configuration file ごとに1回、Python の warnings framework に公開 `ConfigurationDeprecationWarning` を報告します。これは `FutureWarning` subclass のため Python の既定 filter でも表示されます。Base chain から読み込まれた Configuration も対象です。

        Warning location は固定 `stacklevel` に依存せず、dirpluck package 外の最初の caller frame に帰属します。呼び出し側が明示的に制御したい場合は `dirpluck.ConfigurationDeprecationWarning` を category として warning filter に指定できます。この lifecycle diagnostic は planning diagnostic を返す `RunResult.warnings` には含まれません。CLI は同じ診断を収集して簡潔な stderr warning として表示するため、CLI 実行時に追加の Python warning は発行しません。

        旧記法は 1.0.0 で invalid Configuration になります。Shared reference は `{ shared = "..." }`、`ignore` の concrete relative path は `{ path = "..." }` へ移行してください。
        """
        title @= 'Configuration deprecation warning'

    class SECTION_045:
        r"""
        `output` は Configuration の Output destination を invocation 単位で置き換える runtime argument です。

        ```python
        {{exact_output_example}}
        ```

        末尾 `/` がない `output` は exact output file path です。末尾 `/` がある場合は directory として扱い、その directory 直下へ automatic timestamp filename を生成します。

        ```python
        {{directory_output_example}}
        ```

        Automatic filename は、root Configuration が `[output.timestamp]` を持つ場合にその `prefix` / `suffix` naming rule を再利用します。Configured output directory は再利用しません。Root に timestamp Output がなければ `dirpluck-YYYYMMDD-HHMMSS.zip` を使います。`sequence` は automatic timestamp filename にだけ指定できます。

        `output` を指定した build は root Configuration に Output declaration がなくても実行できます。Runtime Output の overwrite は既定で無効です。既存 destination を置き換える場合は `force=True` を指定します。`force=True` は Configuration の fixed / timestamp Output を使う build にも適用できます。

        CLI `--here` は Python API に専用 argumentを持たず、`output="./"` が同じ cwd + automatic filename、`output="context.zip"` が cwd + explicit filename に相当します。`output` path は OS にかかわらず `/` separator を使い、backslash を受理しません。
        """
        title @= 'Runtime Output'

        exact_output_example @= """
        result = dirpluck.run(
            "example",
            output="artifacts/context.zip",
        )
        """
        directory_output_example @= """
        result = dirpluck.run(
            "example",
            output="artifacts/snapshots/",
        )
        """

    class SECTION_005:
        r"""
        Named Invocation も CLI と同じ形で選択できます。

        ```python
        {{invocation_example}}
        ```

        概念的には次と同じです。

        ```console
        {{invocation_cli_example}}
        ```

        Field を持たない Invocation も有効です。その場合、`RunResult.invocation_empty` が `True` になります。CLI はこれを human-readable note として表示しますが、Python API は状態を field で返します。
        """
        title @= 'Invocation Template'

        invocation_example @= """
        import dirpluck

        result = dirpluck.run(
            invocation="calls/release",
            entry="review",
            case="audit",
            preview=True,
        )
        """
        invocation_cli_example @= "dirpluck -i calls/release -e review --case audit --preview"

    class SECTION_055:
        r"""
        `archive_mtime` は CLI `--archive-mtime VALUE` と同じ runtime policy です。

        ```python
        {{archive_mtime_example}}
        ```

        受理する値は `YYYY-MM-DDTHH:MM:SS`、`"now"`、`"zip-epoch"` です。明示 timestamp は ZIP の 1980-01-01T00:00:00 から 2107-12-31T23:59:59 の範囲とし、timezone conversion は行いません。`now` は1回の `run()` で local current time を1度だけ取得します。ZIP timestamp の2秒粒度に合わせ、奇数秒は直前の偶数秒へ切り下げます。

        値を指定すると generated `README.md`、empty directory entry、source file の全 ZIP entry に同じ timestamp を適用します。省略時は source file の filesystem mtime と generated entry の生成時刻を使う従来動作を維持します。固定値は entry timestamp による byte 差を取り除き、reproducible な Archive を作る一助になります。ただし source file の permission bits など他の filesystem metadata は正規化せず、Archive 全体の byte-for-byte reproducibility は保証しません。Timestamp output filename の時刻にも影響しません。`preview=True` でも argument 自体は受理しますが、Archive を書かないため結果には影響しません。
        """
        title @= 'Archive entry の mtime'

        archive_mtime_example @= """
        result = dirpluck.run(
            "example",
            archive_mtime="zip-epoch",
        )
        """
