from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.specification import MUST, level
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary('仕様全体の位置づけ、公開面、関連文書への導線。')


@canonical_source('Specification overview', filename='overview.md', order=0, merge_policy="local", heading="identity")
class SPECIFICATION_PART:
    r"""{{TERM_1}} の CLI、`.dirpluck` {{TERM_2}}形式、`.dirpluck-inv` {{TERM_19}}形式について、互換性対象となる厳密な動作意味論を定義する。両 document の内容は TOML syntax を使用する。 Python package root の公式 API surface と `run()` の呼び出し契約は `../python_api/INDEX.md` に定義し、`run()` が実行する Configuration / Target / Case / Invocation / Archive semantics はこの仕様と共通とする。用途は `../../README.md`、用語の意味は `../../GLOSSARY.md`、Configuration の書き方は `../configuration/INDEX.md`、CLI の操作方法は `../cli/INDEX.md`、Configuration / Invocation Template と filesystem 操作の trust boundary は `../TRUST.md` を参照する。"""
    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2
    merge @= TERMS.TERM_19

    class SECTION_001:
        title @= '公開面'

        class SPEC_001:
            r"""互換性を保証する公開面は `dirpluck` CLI、この文書で定義する `.dirpluck` Configuration document / `.dirpluck-inv` Invocation Template document 形式、および `../python_api/INDEX.md` で明示する package-root Python API とする。両 document の内容は TOML syntax を使用する。Package root から明示的に export しない Python module / name は内部実装として扱う。"""
            level @= MUST
