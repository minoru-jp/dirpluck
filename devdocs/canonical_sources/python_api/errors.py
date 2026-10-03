from shikumi_devdoc.fields.api_reference import TYPE, kind, name
from shikumi_devdoc.fields.lifecycle import introduced
from shikumi_devdoc.norms.common import canonical_source, summary
from shikumi_devdoc.norms.document import test_target_field


error_example = test_target_field("DirpluckError example")


@summary('Python API が公開する error boundary と `DirpluckError`。')
@canonical_source('DirpluckError', filename='errors.md', order=30, merge_policy="local", heading="title")
class API_REFERENCE_PART:
    r"""
    Python API から期待される dirpluck error をまとめて扱う場合は `DirpluckError` を catch します。

    ```python
    {{error_example}}
    ```

    Invalid Configuration、Target / Selection resolution、Invocation Template、または `run()` の互換でない argument combination は `DirpluckError` の subclass を raise します。CLI の status 2 や `dirpluck: error:` prefix は CLI adapter の presentation であり、Python API contract には含めません。
    """

    error_example @= """
    import dirpluck

    try:
        result = dirpluck.run("example", preview=True)
    except dirpluck.DirpluckError as exc:
        print(exc)
    """

    name @= "DirpluckError"
    kind @= TYPE
    introduced @= "0.9.0"
