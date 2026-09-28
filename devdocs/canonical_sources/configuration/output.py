from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_020 = test_target_field("example 020")
example_021 = test_target_field("example 021")


@summary('Fixed / timestamp Output と書き込み境界。')


@canonical_source('Configuration output', filename='output.md', order=40, merge_policy="local", heading="title")
class CONFIGURATION_PART:
    r"""
    この文書は、Configuration が宣言する Output、fixed / timestamp mode、書き込み境界を説明します。

    この guide は Configuration 側の Output authoring を説明し、fixed / timestamp / runtime Output と書き込み境界の厳密な契約は `../specification/output.md` が定義します。CLI runtime Output は `../cli/output.md`、trust boundary は `../TRUST.md` を参照してください。
    """

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2

    class SECTION_014:
        r"""
        {{TERM_9}}は optional です。共通 definition を提供する Base Configurationだけでなく、`--preview` や runtime Output を使う root Configuration でも Output を省略できます。Runtime Output を指定しない通常 build では、root Configuration 自身に fixed mode または timestamp mode のどちらか一方を直接宣言します。Base の Output は継承されません。
        """
        title @= 'Output'

        merge @= TERMS.TERM_9

        class SECTION_015:
            r"""
            ```toml
            {{example_020}}
            ```

            `path` は filename まで含む具体的な output file path です。Relative path はこの `[output]` を記述した Configuration file の directory を基準に解決します。

            `overwrite` は existing output を置き換えてよいかを表し、既定は `false` です。Output file は毎回通常の新規 file creation と同じ permission semantics で作られ、POSIX では process `umask` が適用されます。`overwrite = true` でも置き換える前の file mode は継承しません。`prefix` / `suffix` は fixed mode では使いません。
            """
            title @= 'Fixed output'

            example_020 @= """
            [output]
            path = "artifacts/review.zip"
            overwrite = false
            """

        class SECTION_016:
            r"""
            ```toml
            {{example_021}}
            ```

            `path` は output directory を指定し、末尾 `/` で directory path であることを表します。Relative path はこの definition を記述した Configuration file の directory を基準に解決します。

            Filename は次の形で生成します。

            ```text
            [prefix-]YYYYMMDD-HHMMSS[-N][-suffix].zip
            ```

            `prefix` と `suffix` は timestamp mode 専用です。同じ秒に複数 run を意図的に区別したい場合は CLI `--sequence N` を使えます。CLI `--here` や末尾 `/` の `--output PATH`、Python API の末尾 `/` の `output=` で runtime directory Output を指定した場合も、root Configuration が `[output.timestamp]` を持てば `prefix` / `suffix` は automatic filename の naming rule として再利用されます。Configured `path` は runtime destination には使いません。ZIP entry 自体の mtime を統一する policy は Configuration field ではなく、CLI / Invocation Template の `--archive-mtime` / `archive_mtime` で指定します。
            """
            title @= 'Timestamp output'

            example_021 @= """
            [output.timestamp]
            path = "artifacts/snapshots/"
            prefix = "project"
            suffix = "review"
            """

        class SECTION_160:
            r"""
            Output は、Configuration だけから{{TERM_17}}を静的に確定できる形に限定します。Fixed output では指定した完全 file path、timestamp output では指定した directory tree が書き込み境界です。

            Base chain 上の Output definitions は互いの書き込み境界へ介入できません。Fixed / timestamp の組み合わせごとの overlap 判定は `../specification/INDEX.md` を参照してください。
            """
            title @= 'Writable destination'

            merge @= TERMS.TERM_17
