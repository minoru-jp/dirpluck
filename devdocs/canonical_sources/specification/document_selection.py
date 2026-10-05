from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from shikumi_devdoc.fields.specification import MUST, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary("Configuration と Invocation Template の選択・解決規則。")
@canonical_source(
    "CLI document selection",
    filename="document-selection.md",
    order=10,
    merge_policy="local",
    heading="identity",
)
class SPECIFICATION_PART:
    class SPEC_002:
        r"""Configuration document の filename extension は `.dirpluck` で、内容は TOML syntax とする。`--config` を省略した場合、dirpluck が暗黙に選択する Configuration は process cwd 直下の `default.dirpluck` 1個だけとする。別 directory の `default.dirpluck`、別名の `*.dirpluck`、file 内容から推論した候補は探索・列挙・自動選択しない。cwd の `default.dirpluck` が存在しなければ not-found error とし、`.toml` file への compatibility fallback は提供しない。"""

        level @= MUST

    class SPEC_003:
        r"""`--config PATH` を指定した場合、`PATH` は Filesystem path notation で定める lexical rule を使う1個の Configuration document path とする。Relative path は runtime cwd から、absolute path は host filesystem 上の location として解決する。末尾が `.dirpluck` でなければその suffix を付加するため、`release-1.2` は cwd の `release-1.2.dirpluck`、`configs/release-1.2` は cwd の `configs/release-1.2.dirpluck` を表す。Dot を含む stem を別 extension として拒否しない。Trailing `/`、`.`、`..` のように file name を持たない directory form は受理しない。解決後はその1 path だけを使用し、別 directory の同名 file を探索せず、directory を指定して内部の `default.dirpluck` を補完しない。Document path は host OS の通常の filesystem semantics に従って解決し、symbolic link / Windows directory junction を含む path を特別に拒否しない。Document 内の relative filesystem path は suffix completion 後に選択された Configuration document path の directory を基準に解決する。解決先が既存 regular file でなければ not-found / invalid-file error とする。"""

        level @= MUST
        condition @= "`--config PATH` を指定した場合"
        related @= (PATHS_SPEC.SPEC_017, PATHS_SPEC.SPEC_022, PATHS_SPEC.SPEC_023)

    class SPEC_004:
        r"""{{TERM_19}} document の filename extension は `.dirpluck-inv` とする。Invocation Template file は `-i PATH` / `--invocation-template PATH` で明示した場合だけ使用し、file 自体の implicit default は持たない。`PATH` の lexical rule と relative / absolute resolution は `--config PATH` と同じで、relative path は runtime cwd 基準とする。末尾が `.dirpluck-inv` でなければ suffix を付加し、`set-2.1` は cwd の `set-2.1.dirpluck-inv`、`invocations/release` は cwd の `invocations/release.dirpluck-inv` を表す。解決後はその1 path だけを使用し、別 directory を探索しない。Document path は host OS の通常の filesystem semantics に従い、symbolic link / Windows directory junction を含む path を特別に拒否しない。Invocation Template 内の relative document reference は suffix completion 後に選択された Invocation Template document path の directory を基準に解決する。"""

        merge @= TERMS.TERM_19
        level @= MUST

    class SPEC_005:
        r"""`.dirpluck-inv` document は top-level `invocation` table を必要とする。完全に空の document や top-level `invocation` を持たない document は error とする。TOML の `[invocation.<name>]` declaration により親 `invocation` table が暗黙に成立する場合も、この requirement を満たす。"""

        level @= MUST

    class SPEC_006:
        r"""Root `[invocation]` は `-e` / `--entry` を省略したときに選択する default Invocation とする。`[invocation.<name>]` は `-e NAME` / `--entry NAME` で選択する named Invocation entry とする。Named entry は root Invocation の差分・派生ではなく独立した Invocation であり、未指定 field を root から継承・merge しない。`config`、`targets`、`case`、`archive_mtime` は root Invocation の field 名として予約し、同名を named Invocation entry name として受理しない。指定した named entry が存在しなければ error とする。`-e` / `--entry` は Invocation Template file を選択した実行でだけ受理し、最大1回だけ指定できる。"""

        level @= MUST

    class SPEC_007:
        r"""Default Invocation と各 named entry は `config`、`targets`、`case`、`archive_mtime` だけを field として受理し、4 field はすべて optional とする。Field を1つも持たない Invocation も schema 上および実行上有効とする。`targets` は CLI positional Target reference の array とし、各 element は空でない string で Runtime Target, Scope, and Case の CLI Target reference grammar に従って execution 時に解決する。`case` は CLI `--case CASE` と同じ空でない Case selector とし、`PLUCK` / `.ALWAYS` / `PLUCK.ALWAYS` の2軸 grammar を使用する。`archive_mtime` は Output の Archive entry timestamp rules で定める `--archive-mtime VALUE` と同じ string grammar を使用し、Archive entry timestamp の runtime default とする。`config` は concrete Configuration document path とし、`--config PATH` と同じく末尾が `.dirpluck` でなければ suffix を付加する。Filesystem path notation と同じく `/` separator を使用して glob / backslash を受理しない。Relative `config` path は選択した Invocation Template location の directory、absolute path は host filesystem 上の location を参照し、`~` expansion や environment-variable interpolation は行わない。Control document path の symbolic link / Windows directory junction は host OS の通常の filesystem semantics に従う。"""

        level @= MUST
        related @= (
            PATHS_SPEC.SPEC_017,
            PATHS_SPEC.SPEC_021,
            PATHS_SPEC.SPEC_022,
            PATHS_SPEC.SPEC_023,
        )

    class SPEC_008:
        r"""選択した Invocation が `config` を省略した場合は runtime cwd の `default.dirpluck` を使用し、`targets` を省略した場合は positional Target を与えない実行として扱い、`case` を省略した場合は通常の default Case semantics、`archive_mtime` を省略した場合は通常の Archive entry timestamp semantics を使用する。4 field がすべて未指定でも、CLI から与えた runtime value とこれらの normal defaults を通常どおり適用する。成功した `--preview` または通常 build で field を1つも持たない Invocation が選択されていた場合は、その状態を warning ではない runtime note として CLI output に表示する。"""

        level @= MUST
        condition @= "選択した Invocation が field を省略した場合"

    class SPEC_009:
        r"""Invocation Template を使用する実行では positional `TARGET` と `--config` による差分・override を受理しない。`--case` は選択した Invocation の保存 field override として受理し、指定時はその Invocation の `case` より優先する。`--archive-mtime` も保存 field override として受理し、指定時は Invocation の `archive_mtime` より優先する。`--here` / `--output` / `--force`、`--preview`、`--sequence`、`--archive-mtime`、`--paths` は Template の保存内容を変更しない runtime modifier として通常の制約の範囲で併用できる。"""

        level @= MUST
        condition @= "Invocation Template を使用する実行"

    class SPEC_010:
        r"""{{TERM_13}}の参照では CLI document selection を行わない。各 Configuration は `about.base` に `.dirpluck` extension を持つ concrete Configuration file path を直接記述する。Base path も host OS の通常の filesystem semantics に従い、relative path は参照元 Configuration location の directory を基準にする。`.dirpluck-inv` document は Configuration ではなく base chain に参加しない。"""

        merge @= TERMS.TERM_13
        level @= MUST
