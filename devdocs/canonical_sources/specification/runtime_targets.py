from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.composition import SPECIFICATION_PART as COMPOSITION_SPEC
from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from shikumi_devdoc.fields.specification import MAY, MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary('Scope、Target reference、expansion、Always source、Case の解決規則。')


@canonical_source('Runtime Target, Scope, and Case', filename='runtime-targets.md', order=50, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_037:
        r"""{{TERM_15}}に Pluck が存在する場合は CLI positional `TARGET` reference を1個以上必要とする。Pluck がない Effective Configuration では positional Target reference を受理しない。"""
        merge @= TERMS.TERM_15
        level @= MUST
        condition @= "Effective Configuration に Pluck が存在する場合"
        condition @= "Effective Configuration に Pluck が存在しない場合"

    class SPEC_038:
        r"""各 positional reference は effective Scope から1個以上の{{TERM_3}}を解決し、各 Target へ同じ effective Pluck selection を独立して適用する。Target を Configuration file の配置や Pluck definition の origin から自動推定しない。"""
        merge @= TERMS.TERM_3
        level @= MUST

    class SECTION_501:
        title @= 'Scope'

        class SPEC_039:
            r"""Default Scope は常に1個存在し、{{TERM_14}}がある directory を Scope root とする。Directory name による special case は設けない。`[scope]` はこの default Scope の optional `ignore` / `namespace` だけを設定し、`path` を持たない。`[scope]` を省略した場合と空の `[scope]` は同じ意味で、default Scope の `ignore` は空、Namespace reference はなしとする。"""
            merge @= TERMS.TERM_14
            level @= MUST
            related @= (COMPOSITION_SPEC.SECTION_402.SPEC_030, COMPOSITION_SPEC.SECTION_402.SPEC_032)

        class SPEC_040:
            r"""名前付き `[scope.<name>]` は required `path` と optional `ignore` / `namespace` を持つ。`path` は concrete directory path とし、empty string と glob を拒否する。Relative `path` は Filesystem path notation の共通規則に従って definition の Configuration file directory から解決し、absolute `path` は host filesystem 上の directory を直接参照する。明示された Scope root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で解決した先が実在 directory でなければならない。Scope root 自体が alias であることと、その root 直下で自動発見した link-like Target candidate を除外することは別の rule とする。"""
            level @= MUST
            related @= (PATHS_SPEC.SPEC_018, PATHS_SPEC.SPEC_024)

        class SPEC_041:
            r"""Named Scope の root が実在し directory であることは、その Scope を `SCOPE/NAME` または `SCOPE/` で実際に使用するときに検証する。未使用の named Scope の filesystem availability は、その run を失敗させない。Duplicate effective Scope root の検査は Configuration-level validation として行い、未使用 Scope の存在確認を必要としない。"""
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
            r"""`scope.ignore` は Target candidate の direct child directory **name** を case-sensitive に照合し、一致した directory は単一 Target 選択と全展開のどちらでも Target にできない。File selection の `pluck.ignore` / `always.<name>.ignore` とは独立する。"""
            level @= MUST

        class SPEC_045:
            r"""Scope ignore pattern は `name` (exact)、`name*` (prefix)、`*name` (suffix)、`*name*` (substring) の4形式とする。`*` 単体、path separator、backslash、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!` を拒否する。Empty array は有効とする。"""
            level @= MUST

    class SECTION_502:
        title @= 'CLI Target reference resolution'

        class SPEC_046:
            r"""
            各 positional `TARGET` argument は、次の4形式のいずれかだけを受理する。

            ```text
            NAME
            SCOPE/NAME
            /
            SCOPE/
            ```
            """
            level @= MUST

        class SPEC_047:
            r"""`NAME` は default Scope 直下の directory を1個選ぶ。`SCOPE/NAME` は named Scope `SCOPE` 直下の directory `NAME` を1個選ぶ。`/` は default Scope の全展開、`SCOPE/` は named Scope の全展開とする。"""
            level @= MUST

        class SPEC_048:
            r"""`/` は filesystem root を意味しない。CLI Target reference grammar における default Scope の expansion marker である。`./`、`./NAME`、`/NAME`、`SCOPE/team/NAME` のような別表記、多階層 reference、absolute filesystem path、backslash separator は受理しない。"""
            level @= MUST

        class SPEC_049:
            r"""`NAME` と `/` は常設の default Scope を使う。`SCOPE/NAME` と `SCOPE/` の `SCOPE` は effective named Scope に存在しなければならず、unknown name を別の relative path interpretation へ fallback しない。"""
            level @= MUST

        class SPEC_050:
            r"""Single Target resolution では指定した entry が Scope root の **direct child** にある実在 directory でなければならない。Symbolic link または Windows directory junction として認識した entry は Target として選択せず、明示的な `NAME` / `SCOPE/NAME` がそのような link-like entry を指す場合は error とする。"""
            level @= MUST
            condition @= "single Target を解決する場合"

        class SPEC_051:
            r"""Scope name は Target lookup の識別子であり、それ自体を archive path に暗黙利用しない。Archive placement に outer directory が必要な場合だけ、Scope が明示参照する{{TERM_18}}を使用する。"""
            merge @= TERMS.TERM_18
            level @= MUST_NOT

    class SECTION_503:
        title @= 'Scope expansion'

        class SPEC_052:
            r"""`/` または `SCOPE/` は対応する Scope root の direct child directory entry を列挙し、Scope の `ignore` に一致しないものをそれぞれ独立した Target として展開する。再帰的な directory 列挙は行わず、regular file は Target にしない。"""
            level @= MUST

        class SPEC_053:
            r"""Ignore 対象 entry と、symbolic link / Windows directory junction として認識した entry は Target candidate として扱わない。認識した link-like entry の参照先は解決せず、`/` / `SCOPE/` の展開結果にも含めない。展開結果が0 eligible directory の場合は error とする。"""
            level @= MUST

        class SPEC_054:
            r"""複数 positional Target reference と expansion は同じ run で併用できる。"""
            level @= MAY

    class SECTION_504:
        title @= 'Always source と Case'

        class SPEC_055:
            r"""`[always.<name>].path` は concrete directory path とし、empty string と glob を拒否する。Relative path は Filesystem path notation の共通規則に従って definition の Configuration file directory を基準に解決する。`.` と `..` を使用でき、absolute path は host filesystem 上の directory を直接参照する。明示された Always source root location は symbolic link / Windows directory junction を含んでもよく、host OS の通常の filesystem semantics で実在 directory に解決する。解決した source directory 自体を selection boundary とし、filesystem root 自体は Always source として拒否する。Root location が alias であることは許可するが、その root 内の Selection traversal で遭遇した link-like entry は Filesystem boundary and entry types の link-like entry rule に従って選択・走査しない。"""
            level @= MUST
            related @= (PATHS_SPEC.SPEC_018, PATHS_SPEC.SPEC_024, COMPOSITION_SPEC.SECTION_402.SPEC_032)

        class SPEC_056:
            r"""Always source は optional `namespace` string を持てる。値は effective `[namespace.<name>]` を参照し、source filesystem path と selection boundary は変更しない。Unknown {{TERM_18}} reference は Configuration error とする。"""
            merge @= TERMS.TERM_18
            level @= MUST

        class SPEC_057:
            r"""{{TERM_4}}は{{TERM_15}}全体で0個または1個だけ有効にし、CLI `--case` から選択する。Layer ごとに別 Case を指定する field はない。"""
            merge @= TERMS.TERM_4
            merge @= TERMS.TERM_15
            level @= MUST

        class SPEC_058:
            r"""Case 未指定時は Pluck があれば `[pluck]`、各 Always source は base `[always.<name>]` selection を使う。"""
            level @= MUST
            condition @= "Case を指定しない場合"

        class SPEC_059:
            r"""Case 指定時に Pluck がある場合、同名 `[pluck.case.<name>]` を必須とする。各 Always source は同名 `[always.<name>.case.<name>]` があれば使い、なければ base selection へ fallback する。Pluck がない場合は、少なくとも1個の Always source が同名 Case を定義しなければならない。"""
            level @= MUST
            condition @= "Case を指定する場合"

        class SPEC_060:
            r"""Case selection は base selection の差分ではなく完全な selection とし、`must` / `may` / `ignore` / Shared reference / `allow_empty` を継承しない。"""
            level @= MUST
