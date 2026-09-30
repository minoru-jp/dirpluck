from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_022 = test_target_field("example 022")
example_023 = test_target_field("example 023")


@summary('Configuration 全体を組み合わせた complete example。')


@canonical_source('Configuration examples', filename='examples.md', order=50, merge_policy="local", heading="title")
class CONFIGURATION_PART:
    r"""
    この文書は、主要な Configuration 要素を組み合わせた complete example を示します。

    この文書は複数の authoring concern を一つに組み合わせた例です。各 field の説明はこの Configuration collection、厳密な契約は `../specification/INDEX.md`、CLI 操作は `../cli/INDEX.md`、trust boundary は `../TRUST.md` を参照してください。
    """

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_2

    class SECTION_017:
        r"""
        ```toml
        {{example_022}}
        ```

        ```console
        {{example_023}}
        ```

        CLI の全 option と Configuration / Invocation Template の選択方法は `../cli/INDEX.md`、この Configuration が正確にどう解決・検証されるかは `../specification/INDEX.md` を参照してください。
        """
        title @= 'Complete example'

        example_022 @= """
        [about]
        description = "Materials prepared for reviewing the current project."
        base = "../common/common.dirpluck"

        [shared.ignore]
        python-dev = [
            ".git/",
            ".venv/",
            "__pycache__/",
            "*.pyc",
        ]

        [pluck]
        description = "The project currently under review."
        may = ["README.md", "src/", "tests/"]
        ignore = [{ shared = "python-dev" }]
        allow_empty = true

        [pluck.case.full]
        description = "The project with all review material."
        may = ["README.md", "src/", "tests/", "docs/"]
        ignore = [{ shared = "python-dev" }]
        allow_empty = true

        [scope]
        ignore = ["archive/"]

        [scope.projects]
        path = "/srv/projects"
        ignore = ["archive/", "tmp-*/"]

        [always.guidelines]
        path = "review-guidelines"
        description = "Guidelines used for every review."
        must = ["*.md"]

        [output]
        path = "artifacts/review.zip"
        """

        example_023 @= """
        dirpluck projects/example/
        dirpluck projects/example/ --case full --preview
        dirpluck projects/
        """

        merge @= TERMS.TERM_1
