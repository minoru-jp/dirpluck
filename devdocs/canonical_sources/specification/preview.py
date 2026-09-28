from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.archive import SPECIFICATION_PART as ARCHIVE_SPEC
from devdocs.canonical_sources.specification.composition import SPECIFICATION_PART as COMPOSITION_SPEC
from devdocs.canonical_sources.specification.output import SPECIFICATION_PART as OUTPUT_SPEC
from devdocs.canonical_sources.specification.runtime_targets import SPECIFICATION_PART as RUNTIME_TARGETS_SPEC
from devdocs.canonical_sources.specification.selection import SPECIFICATION_PART as SELECTION_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary('preview mode の出力と副作用境界。')


@canonical_source('Preview', filename='preview.md', order=110, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_145:
        r"""`--preview` は通常実行と同じ base chain resolution、cycle detection、definition composition、Scope lookup / expansion、Target direct-child resolution と Scope ignore filtering、Case selection、file selection、archive planning を使うが、output file / directory を作成・変更しない。Root Configuration に Output declaration がなくても使用できる。`--preview` は Output を解決・書き込みしないため `--here` / `--output` / `--force` / `--sequence` と組み合わせない。`--archive-mtime` は preview でも validation するが、Archive を書かないため preview result には影響しない。"""
        level @= MUST
        condition @= "`--preview` を使用する場合"
        related @= (COMPOSITION_SPEC.SECTION_402.SPEC_028, RUNTIME_TARGETS_SPEC.SPEC_037, SELECTION_SPEC.SPEC_065, ARCHIVE_SPEC.SPEC_098, OUTPUT_SPEC.SPEC_107)

    class SPEC_146:
        r"""不足する通常の `must` path pattern は `[missing]`、不足する通常の `may` path pattern は `[optional missing]` と tree 上に表示する。`{ match = "..." }` のような path ではない Selection expression は `/` を含んでも path component に分解せず、opaque な未一致 Selection entry として別表示する。最終 selection 0件は policy に応じて `empty, allowed` または `empty, would error` と表示する。型 marker の不一致候補が検出された `must` / `may` は selection result の missing / optional missing semantics を変えず、source label を含む non-fatal diagnostic も生成する。CLI `--preview` はそれを warning として stderr へ表示し、Python API の `preview=True` は `RunResult.warnings` に返す。"""
        level @= MUST
        condition @= "`--preview` で selection result を表示する場合"

    class SPEC_147:
        r"""不正 base path、base cycle、duplicate effective Scope root、使用した Scope root の不在、unknown Scope、不正 Target reference、direct-child boundary を外れる Target、未解決 Shared / Namespace reference、不正 source path、Case inconsistency、duplicate final archive root、Output schema / base-chain write-boundary conflict など Configuration と planning の error は preview でも error とする。未使用の named Scope root が現在存在しないことだけでは error にしない。Base depth 自体は error / warning にしない。"""
        level @= MUST
        condition @= "`--preview` で configuration / planning error を検出した場合"
