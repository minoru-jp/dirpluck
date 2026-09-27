from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.api_reference import OPERATION, TYPE, VALUE, input, kind, name, output
from shikumi_devdoc.fields.lifecycle import introduced
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title


package_exports = test_target_field("package-root exports")


@summary('package root の公式 export と内部実装との互換性境界。')


@canonical_source('Package surface', filename='surface.md', order=40, placeholders=False, heading="title")
class API_REFERENCE_PART:
    r"""
    0.10.x の公式 package-root export は次の4名です。

    ```python
    {{package_exports}}
    ```

    `dirpluck.builder`、`dirpluck.config`、`dirpluck.invocation`、underscore module、そこから import できる model / helper は実装上利用されていても公式 API ではありません。これらへ直接依存する code は Beta 中の内部 refactor で変更される可能性があります。

    公式 surface を意図的に小さく保つことで、CLI と同じ高 level capability を Python へ提供しつつ、Configuration model や archive-planning internals を将来整理する余地を残します。
    """

    package_exports @= "from dirpluck import DirpluckError, RunResult, __version__, run"

    name @= "dirpluck"
    kind @= VALUE
    output @= "run"
    output @= "RunResult"
    output @= "DirpluckError"
    output @= "__version__"

    class SECTION_009:
        r"""
        Repository / source distribution では、次の公開文書を参照します。

        - CLI argument と human-readable output: `docs/cli/INDEX.md`
        - Configuration の書き方: `docs/configuration/INDEX.md`
        - Configuration / Target / Case / traversal / Archive / Output の厳密な意味論: `docs/specification/INDEX.md`
        - filesystem 操作と配布時の trust boundary: `docs/TRUST.md`
        - 用語の意味: `GLOSSARY.md`

        Wheel にも同じ公開文書一式を `dirpluck/_docs/` 以下へ同梱します。したがって installed wheel だけでも README、Glossary、CLI / Configuration / Python API guide、Trust model、Specification、CHANGELOG、STATUS を参照できます。
        """
        title @= '次に読む文書'

