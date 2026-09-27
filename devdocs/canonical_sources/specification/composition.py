from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.document_selection import SPECIFICATION_PART as DOCUMENT_SELECTION_SPEC
from devdocs.canonical_sources.specification.paths import SPECIFICATION_PART as PATHS_SPEC
from shikumi_devdoc.fields.specification import MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary('Base chain、cycle detection、definition composition、Output の扱い。')


@canonical_source('Base chain and composition', filename='composition.md', order=40, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_025:
        r"""{{TERM_13}}は `[about].base` として宣言する。`base` は concrete Configuration file path とし、空文字列と glob を拒否する。Relative path は Filesystem path notation の共通規則に従って現在の Configuration file directory から解決し、absolute path は host filesystem 上の file を直接参照する。Path は `.dirpluck` extension を必要とし、host OS の通常の filesystem semantics に従って参照する。解決先は実在 regular file で、内容が有効な TOML Configuration schema でなければならない。"""
        merge @= TERMS.TERM_13
        level @= MUST
        related @= (DOCUMENT_SELECTION_SPEC.SPEC_003, PATHS_SPEC.SPEC_018)

    class SPEC_026:
        r"""各 Configuration が参照できる base は0個または1個とする。Base Configuration がさらに `base` を持つ場合は linear chain を形成する。Depth に固定上限は設けない。"""
        level @= MUST

    class SECTION_401:
        title @= 'Cycle detection'

        class SPEC_027:
            r"""Base resolution では、診断と relative path resolution のために各 Configuration の選択された document location を保持しつつ、cycle identity は symbolic link / junction alias を解決した実体 file path で比較する。alias 解決後に同じ physical Configuration path となる Configuration が別の document path alias から現在の chain に再登場した場合も cycle error とし、診断には選択された document location の chain を含める。Depth 自体による error / warning は行わない。"""
            level @= MUST
            condition @= "base chain の cycle identity を判定する場合"

    class SECTION_402:
        title @= 'Definition composition'

        class SPEC_028:
            r"""Chain の最深部を初期値とし、1 layer ずつ外側の definition を重ねて{{TERM_15}}を構成する。"""
            merge @= TERMS.TERM_15
            level @= MUST

        class SPEC_029:
            r"""`[about].description` は outermost layer から inner layer へ探索し、最初に定義された値を effective description とする。Chain 全体に定義がなければ effective description は存在しない。`about.base` は chain link であり effective value として shadow / merge しない。Base layer に書かれた `[scope]` はその Configuration 自身を Root として使う場合の default Scope 設定であり、outer Root の default Scope へ継承しない。"""
            level @= MUST

        class SPEC_030:
            r"""
            - Pluck: outer layer に Pluck があれば inner Pluck definition 全体を shadow する。
            - Always source: 同名 source は outer layer が definition 全体を shadow し、異なる名前は保持する。
            - Named Scope: 同名 Scope は outer layer が `description` / `target_kind` / `path` / `ignore` / `namespace` を含む definition 全体を shadow し、異なる名前は保持する。Default Scope は compose せず、Runtime Target, Scope, and Case の default Scope rule に従って Root Configuration location から root を決め、root Configuration の `[scope]` に書かれた `description` / `target_kind` / `ignore` / `namespace` だけを使う。
            - {{TERM_18}}: 同名 Namespace は outer layer が definition 全体を shadow し、異なる名前は保持する。Scope / Always の Namespace reference は composition 後の effective Namespace 集合に対して解決する。
            - Shared pattern: `must` / `may` / `ignore` を独立した namespace とし、各 namespace の同名 pattern set は outer layer が配列全体を shadow する。
            """
            merge @= TERMS.TERM_18
            level @= MUST

        class SPEC_031:
            r"""Pluck / Always / named Scope / {{TERM_18}} の shadow は field 単位の partial merge ではない。Source definition の Case も source definition と一緒に置き換える。"""
            merge @= TERMS.TERM_18
            level @= MUST_NOT

        class SPEC_032:
            r"""Named Scope root と Always source path は、その definition を記述した Configuration file の directory を基準として解決する。Base から残った definition は origin の resolution result を保持し、outer layer へ rebase しない。Default Scope は path field を持たず、Runtime Target, Scope, and Case の default Scope rule で root を決める。"""
            level @= MUST
            related @= (PATHS_SPEC.SPEC_018,)

        class SPEC_033:
            r"""Composition 後の effective Scope 群について、filesystem 上の存在を要求せずに path を解決・正規化した Scope root が同一 location になる定義を複数持つことはできない。Default Scope と named Scope の組み合わせにもこの rule を適用する。親子関係にある異なる directory は、この duplicate rule だけでは同一とはみなさない。"""
            level @= MUST
            condition @= "composition 後の effective Scope root を検証する場合"

        class SPEC_034:
            r"""Selection の Shared reference は、source の origin layer ではなく chain 全体を重ね終えた effective shared namespace で解決する。Outer layer は inner source が参照する同名 pattern set を提供または shadow できる。"""
            level @= MUST

    class SECTION_403:
        title @= 'Output と base chain'

        class SPEC_035:
            r"""Output definition は source definition のようには compose しない。Configuration は Output を省略でき、共通 definition だけを提供する Base Configuration として利用できる。Archive planning と `--preview` は root Output を必要としない。実際に Archive file を書き込む build で使用するのは{{TERM_14}}自身が直接宣言した Output だけとし、root が Output を持たない場合は build error とする。Inner layer の Output を root へ継承しない。"""
            merge @= TERMS.TERM_14
            level @= MUST
            condition @= "Archive file を書き込む build"

        class SPEC_036:
            r"""Base chain 上では、Output を宣言している Configuration の definition だけを各 Configuration の書き込み所有境界として保持し、Output の base-chain write-boundary overlap rules で chain 内の{{TERM_17}}が overlap しないことを検証する。Output を宣言しない layer は write boundary を持たない。"""
            merge @= TERMS.TERM_17
            level @= MUST
