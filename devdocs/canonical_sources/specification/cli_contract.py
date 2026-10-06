from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.document_selection import (
    SPECIFICATION_PART as DOCUMENT_SELECTION_SPEC,
)
from devdocs.canonical_sources.specification.output import SPECIFICATION_PART as OUTPUT_SPEC
from devdocs.canonical_sources.specification.preview import SPECIFICATION_PART as PREVIEW_SPEC
from devdocs.canonical_sources.specification.runtime_targets import (
    SPECIFICATION_PART as RUNTIME_TARGETS_SPEC,
)
from devdocs.canonical_sources.specification.composition import (
    SPECIFICATION_PART as COMPOSITION_SPEC,
)
from shikumi_devdoc.fields.specification import MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary("CLI options、組み合わせ制約、exit behavior の契約。")
@canonical_source(
    "CLI contract", filename="cli-contract.md", order=120, merge_policy="local", heading="identity"
)
class SPECIFICATION_PART:
    class SPEC_148:
        r"""
        CLI が受理する主な form は次とする。

        ```console
        dirpluck TARGET [TARGET ...]
        dirpluck --config PATH
        dirpluck TARGET [TARGET ...] --case CASE
        dirpluck --config PATH --case CASE
        dirpluck -i PATH [-e NAME] [--case CASE]
        dirpluck --invocation-template PATH [--entry NAME] [--case CASE]
        dirpluck ... --preview
        dirpluck ... --paths
        dirpluck ... --sequence N
        dirpluck ... --archive-mtime VALUE
        dirpluck ... --here[=FILENAME]
        dirpluck ... -o PATH
        dirpluck ... --output PATH
        dirpluck ... -f
        dirpluck ... --force
        dirpluck --version
        ```
        """

        level @= MUST

    class SPEC_149:
        r"""Positional argument は Runtime Target, Scope, and Case の CLI Target reference rules で解決する。Positional Target reference は常に0個以上を受理する。0個の場合は Pluck を source selection に使用せず、通常参加する Always source と選択した Always Case の `include` / `add` で有効化された Extra source があれば、それら fixed source だけを解決する。参加する fixed source もなければ resolved source 0件の README-only Archive として正常に実行する。Target reference を指定した場合、Pluck がない Configuration でも `target_kind = "file"` / `"both"` の Scope から file Target reference は受理するが、directory Target は受理しない。"""

        level @= MUST
        condition @= "positional Target reference を0個または1個以上指定する場合"
        related @= (RUNTIME_TARGETS_SPEC.SPEC_037,)

    class SPEC_150:
        r"""`--case`、`--sequence`、`--archive-mtime`、`--here`、`-o` / `--output`、`-i` / `--invocation-template`、`-e` / `--entry` はそれぞれ最大1回だけ指定できる。`-e` / `--entry` は Invocation Template と一緒にだけ使用できる。Invocation Template を指定した場合は positional `TARGET` と `--config` を受理しない。`--case` は Invocation Template と併用でき、指定時は選択した Invocation の `case` を上書きする。`--archive-mtime VALUE` も Invocation Template と併用でき、指定時は選択した Invocation の `archive_mtime` を上書きする。`VALUE` は Output の Archive entry timestamp grammar に従う。`--here` と `--output` は相互排他とし、`--here` の optional filename は `--here=FILENAME` の form でだけ指定する。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--sequence` は1以上の integer を受理し、automatic timestamp filename の effective Output でだけ使用する。`-f` / `--force` は effective overwrite policy を true にする。`--here` / `--output` / `--force`、`--preview`、`--sequence`、`--archive-mtime`、`--paths` は Invocation Template と併用できる。`--paths` は通常 build で生成する{{TERM_10}}の各 source section へ `Source` metadata を追加する。`--preview` と組み合わせても Archive は生成されないため、表示 tree に source filesystem path を追加しない。"""

        merge @= TERMS.TERM_10
        level @= MUST
        related @= (
            DOCUMENT_SELECTION_SPEC.SPEC_009,
            OUTPUT_SPEC.SECTION_902.SPEC_122,
            OUTPUT_SPEC.SECTION_9022.SPEC_129,
            OUTPUT_SPEC.SECTION_9025.SPEC_131,
            OUTPUT_SPEC.SECTION_9025.SPEC_132,
            PREVIEW_SPEC.SPEC_145,
        )

    class SPEC_151:
        r"""Argument parse error と dirpluck の Configuration / build error は status 2 で終了する。Successful build と informational command は status 0 とする。通常 build の成功時は final output path を標準出力から取得できるようにする。Resolved source が0件なら、通常 build / `--preview` のどちらでも `README.md` だけの Archive plan になったことを informational output として扱い、warning semantics は与えない。Field を1つも持たない Invocation を選択した成功実行では、保存済み実行入力がなく CLI runtime value と normal defaults を使うことを informational note として示す。これらの人間向け文言と表示順序の細部は互換性契約に含めない。"""

        level @= MUST
        condition @= "CLI execution が終了する場合"

    class SPEC_152:
        r"""Base chain 用の追加 CLI path や layer ごとの Case option は提供しない。Base chain は TOML の `about.base`、Case は composition 後の{{TERM_15}}へ適用する。"""

        merge @= TERMS.TERM_15
        level @= MUST_NOT
        related @= (COMPOSITION_SPEC.SPEC_025, COMPOSITION_SPEC.SECTION_402.SPEC_030)
