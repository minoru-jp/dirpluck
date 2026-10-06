from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title


basic_run_example = test_target_field("basic run example")
basic_cli_example = test_target_field("basic CLI equivalent")
cwd_example = test_target_field("cwd example")


@summary("公式 Python API の位置づけ、基本的な呼び出し方、互換性境界。")
@canonical_source(
    "Python API overview", filename="overview.md", order=0, merge_policy="local", heading="title"
)
class API_REFERENCE_PART:
    r"""
    この文書は、{{TERM_1}} 0.17.x の公式 Python API を説明します。API は CLI と同じ実行 model を Python から利用するための最小 surface として定義し、Configuration parser や builder pipeline の低 level object を一般用途の互換性契約には含めません。

    `run()` の引数と runtime modifier は `run.md`、返り値は `result.md`、公開 error boundary は `errors.md`、package root の互換性対象 export は `surface.md` を参照してください。Configuration / Target / Case / Archive の実行意味論は `../specification/INDEX.md` と共通です。
    """

    merge @= TERMS.TERM_1

    class SECTION_002:
        r"""
        公式 API の中心は `dirpluck.run()` です。CLI が受け取る Target、Configuration、Case、Invocation Template、Entry、preview、output modifier を Python argument として渡し、同じ application layer で実行します。

        CLI は人間向けの argument parsing、help、exit status、stdout / stderr formatting を担当します。Python API は `SystemExit` を通常の制御手段にせず、結果を `RunResult` で返し、期待される dirpluck error を `DirpluckError` として raise します。Non-fatal な planning diagnostic は `RunResult.warnings` に返し、CLI は同じ warning を stderr へ表示します。Configuration / migration lifecycle の warning は Python の warnings framework で報告し、CLI は同じ public warning を収集して stderr へ表示します。

        0.17.x では、package root から明示的に export する名前だけを公式 Python API とします。低 level module や underscore 名は implementation detail であり、Beta 中の互換性保証対象には含めません。
        """

        title @= "位置づけ"

    class SECTION_003:
        r"""
        ```python
        {{basic_run_example}}
        ```

        これは概念的に次の CLI invocation と同じです。

        ```console
        {{basic_cli_example}}
        ```

        `config` を省略した場合は runtime cwd の `default.dirpluck` を使います。Python API では process cwd を変更せずに relative document path の基準だけを指定したい場合、API 専用の `cwd` argument を使えます。

        ```python
        {{cwd_example}}
        ```

        この `config` は `/work/project/configs/review.dirpluck` を選びます。`cwd` は Configuration 内の relative source path の基準を変更しません。それらは通常どおり各 Configuration document location を基準に解決します。
        """

        title @= "基本形"

        basic_run_example @= """
        import dirpluck

        result = dirpluck.run("example")
        print(result.output_path)
        """
        basic_cli_example @= "dirpluck ./example/"
        cwd_example @= """
        from pathlib import Path
        import dirpluck

        result = dirpluck.run(
            "example",
            config="configs/review",
            cwd=Path("/work/project"),
        )
        """
