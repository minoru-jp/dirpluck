from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.specification import MAY, MUST, level
from shikumi_devdoc.norms.common import canonical_source, merge, summary


@summary('Archive placement に使用する Namespace の定義と制約。')
@canonical_source('Namespace', filename='namespace.md', order=60, merge_policy="local", heading="identity")
class SPECIFICATION_PART:
    class SPEC_061:
        r"""{{TERM_18}}は `[namespace.<name>]` という名前付き table で定義する。現行 schema では table 本体は空でなければならず、属性を受理しない。親 `[namespace]` だけを空で定義することは Namespace definition にならないため error とする。"""
        merge @= TERMS.TERM_18
        level @= MUST

    class SPEC_062:
        r"""Namespace name はそのまま ZIP 内の directory component になる。空名、`.`、`..`、`/`、backslash、control character、portable filename component として不適切な `< > : " | ? *` を拒否する。Namespace は filesystem path ではなく Archive path の1 component である。"""
        level @= MUST

    class SPEC_063:
        r"""Scope / Always source の `namespace` field は effective Namespace name を参照する。Namespace を参照した source の final archive root は `NAMESPACE/SOURCE_ROOT` とする。この prefix は他 source との衝突有無にかかわらず常に適用する。Namespace を参照しない source の final archive root は `SOURCE_ROOT` のままとする。"""
        level @= MUST

    class SPEC_064:
        r"""複数 source が同じ Namespace を参照すること自体は有効である。ただし Namespace は自動 collision resolver ではなく、final archive root の一意性は Archive planning の final archive root uniqueness rule で検証する。"""
        level @= MAY
