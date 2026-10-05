from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.composition import (
    SPECIFICATION_PART as COMPOSITION_SPEC,
)
from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from shikumi_devdoc.fields.specification import MAY, MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary("Scope、Target reference、expansion、Always source、Case の解決規則。")
@canonical_source(
    "Runtime Target, Scope, and Case",
    filename="runtime-targets.md",
    order=50,
    merge_policy="local",
    heading="identity",
)
class SPECIFICATION_PART:
    class SPEC_037:
        r"""CLI positional `TARGET` reference は0個以上とする。Target reference が0個の run では Pluck は source selection に参加せず、Always source があればそれらだけを解決する。Always source もなければ resolved source は0個となり、build は generated `README.md` だけを含む Archive として正常に成立する。Target reference を指定した場合は従来どおり Scope / Target resolution を行い、directory Target は Pluck を必要とする。Pluck がない Effective Configuration でも `target_kind = "file"` / `"both"` の Scope から file Target を選ぶ positional Target reference は受理する。"""

        merge @= TERMS.TERM_15
        level @= MUST
        condition @= "Target reference を0個または1個以上指定する場合"

    class SPEC_038:
        r"""各 positional reference は effective Scope から1個以上の{{TERM_3}}を解決する。Directory Target には同じ effective Pluck selection を独立して適用し、file Target には Pluck を適用せず regular file 自体を atomic source とする。Pluck がない場合に directory Target を解決しようとした run は error とする。Target を Configuration file の配置や Pluck definition が記述された Configuration から自動推定しない。"""

        merge @= TERMS.TERM_3
        level @= MUST

    class SECTION_501:
        title @= "Scope"

        class SPEC_039:
            r"""Default Scope は常に1個存在し、{{TERM_14}}がある directory を Scope root とする。Directory name による special case は設けない。`[scope]` はこの default Scope の optional `description` / `target_kind` / `ignore` / `namespace` を設定し、`path` を持たない。`target_kind` の既定は `"directory"` とする。`[scope]` を省略した場合と空の `[scope]` は同じ意味で、description なし、directory Target、`ignore` は空、Namespace reference はなしとする。"""

            merge @= TERMS.TERM_14
            level @= MUST
            related @= (COMPOSITION_SPEC.SECTION_402.SPEC_030,)

        class SPEC_040:
            r"""名前付き `[scope.<name>]` は required `path` と optional `description` / `target_kind` / `ignore` / `namespace` を持つ。`target_kind` は `"directory"` / `"file"` / `"both"` のいずれかとし、既定は `"directory"` とする。`path` は concrete directory path とし、empty string と glob を拒否する。Relative `path` は Filesystem path notation の共通規則に従って definition の Configuration file directory から解決し、absolute `path` は host filesystem 上の directory を直接参照する。明示された Scope root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で解決した先が実在 directory でなければならない。Scope root 自体が alias であることと、その root 直下で自動発見した link-like Target candidate を除外することは別の rule とする。`description` は空でない string とし Target discovery / Archive placement を変更しない。"""

            level @= MUST
            related @= (PATHS_SPEC.SPEC_018, PATHS_SPEC.SPEC_024)

        class SPEC_041:
            r"""Named Scope の root が実在し directory であることは、その Scope を `SCOPE/NAME`、`SCOPE/NAME/`、`SCOPE/`、`SCOPE:[...]`、`SCOPE:<...>` のいずれかで実際に使用するときに検証する。未使用の named Scope の filesystem availability は、その run を失敗させない。異なる Scope が同じ filesystem directory を root として参照すること自体は error としない。"""

            level @= MUST
            condition @= "named Scope を実際に使用する場合"

        class SPEC_042:
            r"""Scope name は CLI Target reference の1 path segment として使用できる空でない名前とし、`.`、`..`、`/`、backslash を含めない。"""

            level @= MUST

        class SPEC_043:
            r"""Default / named Scope の `namespace` は optional string とし、effective `[namespace.<name>]` の名前を参照する。{{TERM_18}} reference は Target の探索 root、Target candidate、CLI Target reference の意味には影響せず、Archive placement だけに使用する。Unknown Namespace reference は Configuration error とする。"""

            merge @= TERMS.TERM_18
            level @= MUST

        class SPEC_044:
            r"""`scope.ignore` は Scope 直下の Target candidate name を case-sensitive に照合する。末尾 `/` のない pattern は matching file / directory candidate の両方へ適用し、末尾 `/` の pattern は directory candidate だけに限定する。一致した entry は single Target、Scope expansion、Target selector のいずれでも Target にできない。`scope.ignore` は現在の `target_kind` で eligible な direct-child candidate に対する除外条件とする。Selection の `pluck.ignore` / `always.<name>.ignore` とは独立する。"""

            level @= MUST

        class SPEC_045:
            r"""Scope ignore pattern は broad form の `name` / `name*` / `*name` / `*name*` と、その body の末尾に `/` を付けた directory-only form を受理する。Broad form は matching file / directory candidate の両方へ適用する。`*` 単体、`*/`、path separator を body に含む pattern、backslash、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!` を拒否する。Empty array は有効とする。"""

            level @= MUST

    class SECTION_502:
        title @= "CLI Target reference resolution"

        class SPEC_046:
            r"""
            各 positional `TARGET` argument は、次の形式を受理する。

            ```text
            NAME
            ./NAME
            ./NAME/
            SCOPE/NAME
            SCOPE/NAME/
            /
            SCOPE/
            :[ITEM/ITEM/...]
            SCOPE:[ITEM/ITEM/...]
            :<REGEX>
            SCOPE:<REGEX>
            ```

            Literal entry reference では末尾 `/` なしを file、末尾 `/` ありを directory とし、filesystem 上の実体型から Target type を推測しない。`:[...]` / `SCOPE:[...]` と `:<...>` / `SCOPE:<...>` は Scope の eligible direct-child Target candidate に適用する Target selector とし、`target_kind = "directory"` / `"file"` / `"both"` のすべてで使用できる。
            """

            level @= MUST

        class SPEC_047:
            r"""`NAME` または `./NAME` は default Scope の direct-child **file** Targetを1個選び、`./NAME/` は default Scope の direct-child **directory** Targetを1個選ぶ。`SCOPE/NAME` は named Scope の file Target、`SCOPE/NAME/` は directory Targetを1個選ぶ。`/` は default Scope の全展開、`SCOPE/` は named Scope の全展開とする。`:[...]` / `SCOPE:[...]` は typed literal Target list、`:<...>` / `SCOPE:<...>` は normalized Target name に対する regular-expression selector とする。"""

            level @= MUST

        class SPEC_048:
            r"""`/` は filesystem root を意味せず default Scope の expansion marker とする。`SCOPE/` は named Scope expansion であるため、default Scope の directory Target は `./NAME/` で明示する。`./NAME` は default Scope file Target の明示形として受理する。`/NAME`、`SCOPE/team/NAME` のような多階層 literal reference、absolute filesystem path は受理しない。Literal Target name と list selector の item では backslash を path separator として受理しない。Regular-expression selector 内の backslash は regex escape として使用できる。"""

            level @= MUST

        class SPEC_049:
            r"""`NAME` / `./NAME` / `./NAME/`、`/`、`:[...]`、`:<...>` は常設の default Scope を使う。`SCOPE/NAME` / `SCOPE/NAME/`、`SCOPE/`、`SCOPE:[...]`、`SCOPE:<...>` の `SCOPE` は effective named Scope に存在しなければならず、selector reference や `SCOPE/` を別の relative path interpretation へ fallback しない。"""

            level @= MUST

        class SPEC_050:
            r"""Single Target resolution では syntax が要求する entry type と Scope の `target_kind` の両方を満たす direct child が必要である。末尾 `/` なしの literal reference は regular file、末尾 `/` ありは regular directory を要求する。`target_kind = "directory"` は file reference、`target_kind = "file"` は directory reference を拒否し、`"both"` は両方を許す。Symbolic link または Windows junction として認識した entry は Target として選択せず、明示 reference がそのような link-like entry を指す場合は error とする。特殊 filesystem entry も error とする。"""

            level @= MUST
            condition @= "single Target を解決する場合"

        class SPEC_051:
            r"""Scope name は Target lookup の識別子であり、それ自体を archive path に暗黙利用しない。Archive placement に outer directory が必要な場合だけ、Scope が明示参照する{{TERM_18}}を使用する。"""

            merge @= TERMS.TERM_18
            level @= MUST_NOT

        class SPEC_153:
            r"""Target selector は `target_kind = "directory"` / `"file"` / `"both"` のすべての Scope で有効とし、selector はその Scope の type filter を通った candidate だけを対象とする。"""

            level @= MUST

        class SPEC_154:
            r"""List selector は最外郭の `[` と `]` だけを selector syntax とする。Item の末尾 `/` なしは file、末尾 `/` ありは directory とし、item separator にも `/` を使うため、途中の directory item は `NAME//NEXT` のように directory marker と separator が2連の `/` になる。末尾 directory item は `NAME/]` とする。3連以上の `/`、empty list、empty item、missing closing `]`、存在しない entry、Scope `ignore` に一致する entry、現在の `target_kind` で許可されない entry type は error とする。内部の `[` / `]` / `<` / `>` / `,` / `:` などは Target name の通常文字として扱う。"""

            level @= MUST

        class SPEC_155:
            r"""Regular-expression selector は最外郭の `<` と `>` だけを selector syntax とし、その内部を Python-compatible regular expression として解釈する。Pattern は Scope `ignore` と link-like exclusion を適用済みの eligible direct-child Target の normalized name **全体**へ full-match semantics で適用する。Regular file candidate は `NAME`、regular directory candidate は `NAME/` として照合するため、`/?` など通常の regular-expression syntax で両方を明示的に match できる。Pattern は non-empty、512 character 以下とし、invalid regular expression と0件 match は error とする。`/` は directory type markerとして pattern 内で使用できるが、candidate discovery は Scope 直下に限定され再帰探索しない。"""

            level @= MUST

        class SPEC_156:
            r"""Target selector の対象集合は、`target_kind`、Scope `ignore`、regular entry requirement、link-like exclusion をすべて満たす eligible direct-child Target とする。Selector はこの集合から Target を選び、再帰探索は行わない。`target_kind = "both"` で selector が directory と file を同時に選んだ場合も、directory Target には Pluck Selection を適用し、file Target は atomic source として扱う。"""

            level @= MUST

        class SPEC_157:
            r"""`:` は Target reference の Scope/selector 境界で `:[` または `:<` の selector marker として現れる場合だけ Target selector syntax を開始する。`SCOPE/NAME` の `NAME` 内部を含む、それ以外の `:` は literal Target name の通常文字として扱い、既存の `foo:bar` や `SCOPE/foo:[bar]` のような literal name の意味を変更しない。Selector syntax と同じ形を持つ literal default-Scope Target name を明示する必要がある場合は list selector の1 item として指定できる。"""

            level @= MUST

    class SECTION_503:
        title @= "Scope expansion"

        class SPEC_052:
            r"""`/` または `SCOPE/` は対応する Scope root の direct child entry を列挙し、Scope の `target_kind` と `ignore` に従う eligible entry をそれぞれ独立した Target として展開する。`target_kind = "directory"` では regular directory だけ、`target_kind = "file"` では regular file だけ、`target_kind = "both"` ではその両方を対象とし、再帰列挙は行わない。"""

            level @= MUST

        class SPEC_053:
            r"""Ignore 対象 entry と、symbolic link / Windows junction として認識した entry は Target candidate として扱わない。認識した link-like entry の参照先は解決せず、`/` / `SCOPE/` の展開結果にも含めない。現在の `target_kind` に対応する eligible direct child が0件の場合は error とする。"""

            level @= MUST

        class SPEC_054:
            r"""複数 positional Target reference、Scope expansion、Target selector は同じ run で併用できる。"""

            level @= MAY

        class SPEC_158:
            r"""Target selector と literal Target reference、または複数 Target selector が同じ filesystem entry を選んだ overlap は、その entry を1個の Target として扱い、Selection / Archive へ重複参加させない。Selector を含まない literal Target reference 同士が同じ filesystem entry を重複指定した場合は distinct-entry validation error とする。"""

            level @= MUST

    class SECTION_504:
        title @= "Always source と Case"

        class SPEC_055:
            r"""`[always.<name>]` の `<name>` は TOML key として解釈された後、1個の Archive directory component とし、Always source の logical Archive identity を表す。空名、`.`、`..`、path separator の `/` と `\`、ASCII control character U+0000..U+001F と U+007F は Archive identity として拒否する。これらは host OS 固有の filename rule ではなく、Archive entry name を安全な1 componentとして保持するための制約である。dirpluck は host OS 固有の予約名やその他の filename rule を独自判定しない。`path` は concrete directory path とし、empty string と glob を拒否する。Relative path は Filesystem path notation の共通規則に従って definition の Configuration file directory を基準に解決し、`.` と `..` を使用できる。Absolute path は host filesystem 上の directory を直接参照でき、filesystem root も明示的な source directory として使用できる。明示された Always source location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で実在 directory に解決する。解決した source directory 自体を Selection boundary とし、その directory name は Archive identity に使用しない。Root location が alias であることは許可するが、その root 内の Selection traversal で遭遇した link-like entry は Filesystem boundary and entry types の link-like entry rule に従って選択・走査しない。"""

            level @= MUST
            related @= (PATHS_SPEC.SPEC_018, PATHS_SPEC.SPEC_024)

        class SPEC_057:
            r"""Runtime Case selector は Pluck Case と Always Case の2軸を独立に指定する。`PLUCK` は Pluck Case だけ、`.ALWAYS` は Always Case だけ、`PLUCK.ALWAYS` は両方を指定する。Case name 自身に `.` は使用できない。空 selector、`.`、末尾 dot、2個以上の dot を持つ selector は error とする。CLI `--case`、公式 Python API の `case=`、Invocation の `case` field は同じ grammar を使用する。"""

            merge @= TERMS.TERM_4
            level @= MUST

        class SPEC_058:
            r"""Pluck Case を指定しない場合、directory Target がある run は `[pluck]` の default Selection を使う。Pluck Case を指定した場合は effective `[case.pluck.<name>]` の完全な Selection を使い、Case name が存在しなければ error とする。Pluck Case の validity は Target 数や Always source の有無から独立して判定し、Case が定義済みなら Target が0件でも selector 自体は有効とする。"""

            level @= MUST

        class SPEC_059:
            r"""Always Case を指定しない場合は effective Always source をすべて参加させる。Always Case を指定した場合は effective `[case.always.<name>]` を使い、Case name が存在しなければ error とする。Always Case は source 個別の Selection を置き換えず、effective Always source 集合の membership だけを決める。`include` と `exclude` は同時に指定できない。`include` は記載した Always identifier だけを参加させ、`include = []` は0件を明示する。`exclude` は記載した identifier を除外し、`exclude = []` は何も除外しない。両 field を省略した Case はすべての Always source を参加させる。参照名は final archive root から導出した別名ではなく TOML の Always identifier とし、Base composition 後の effective Always source 集合に存在しない参照は Configuration error とする。"""

            level @= MUST

        class SPEC_060:
            r"""`[case.pluck.<name>]` は base `[pluck]` の差分ではなく完全な Selection とし、`must` / `may` / `ignore` / Shared reference / `allow_empty` を継承しない。`[case.always.<name>]` は Selection ではなく Always source membership filter であり、選択された各 Always source は自身の base Selection をそのまま使用する。Pluck Case / Always Case のどちらも、定義済み Case の結果として participating source が0件になることを許可し、README-only Archive を正常な結果として扱う。"""

            level @= MUST
