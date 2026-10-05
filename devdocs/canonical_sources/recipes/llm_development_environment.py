from shikumi_devdoc.norms.common import canonical_source, summary
from shikumi_devdoc.norms.document import test_target_field, title


configuration_example = test_target_field("configuration example")
offline_commands = test_target_field("offline commands")
online_commands = test_target_field("online commands")


@summary(
    "ネットワーク制限のあるLLM sandbox向けにoffline wheelhouseを同梱し、Always Caseで切り替えるRecipe。"
)
@canonical_source(
    "Recipe: LLM 開発環境へ project を渡す",
    filename="llm-development-environment.md",
    order=10,
    merge_policy="local",
    heading="title",
)
class RECIPE:
    r"""
    このRecipeでは、同じPython projectを異なるLLM sandboxへ渡すときに、package indexへ接続できるかどうかでoffline wheelhouseを切り替えます。

    2026年10月の具体例として、defaultではpackage indexへ接続できないChatGPT sandboxを想定し、`shikumi`、`shikumi-devdoc`、`basedpyright`、`ruff`と必要なdependency wheelを同梱します。`.claude` Always Caseではpackage indexからinstallできる環境を想定し、wheelhouseを除外します。

    長期的に重要なのは製品名ではなく、**offline環境とonline環境を切り替える**考え方です。利用するsandboxの能力が変わった場合は、Case名やdefaultを実環境に合わせて変更してください。
    """

    class SECTION_001:
        r"""
        次のworkspaceを使います。

        ```text
        workspace/
        ├── default.dirpluck
        ├── offline_wheels/
        │   ├── shikumi-0.2.4-py3-none-any.whl
        │   ├── shikumi_devdoc-0.3.5-py3-none-any.whl
        │   ├── basedpyright-1.40.1-py3-none-any.whl
        │   ├── ruff-0.16.10-...whl
        │   └── ... target環境で必要なdependency wheel
        └── project/
            ├── README.md
            ├── pyproject.toml
            ├── src/
            └── tests/
        ```

        `project/`がLLMへ渡す開発対象です。`offline_wheels/`にはoffline installに必要なwheelを事前に用意し、直接依存4個だけでなくtarget環境で必要なtransitive dependencyも含めます。
        """

        title @= "Workspace"

    class SECTION_002:
        r"""
        目的は次の通りです。

        - package indexへ接続できないsandboxでもdefault Archiveだけで開発環境を準備できるようにする。
        - LLMが最初に従うenvironment setupとverificationの指示をArchive READMEの先頭へ置く。
        - package indexを利用できる環境では不要なwheelhouseを除外する。
        - project自体のSelectionは両環境で変えない。

        `about.description`はSelection semanticsを変えませんが、生成されるArchive `README.md`の先頭に挿入されます。短いlabelだけでなく、受け取るLLM向けの複数行の作業指示にも使えます。
        """

        title @= "Goal"

    class SECTION_003:
        r"""
        `default.dirpluck`を次のようにします。

        ```toml
        {{configuration_example}}
        ```

        `[always.offline_wheels]`は選択Targetに関係なくwheelhouseを追加します。Always sourceのidentifierが`offline_wheels`なのでArchive rootも`offline_wheels/`です。

        `[case.always.claude]`は各Always sourceのSelectionを変えるのではなく、参加するAlways source集合から`offline_wheels`だけを外します。`.claude`はAlways Caseだけを選択するCase selectorです。

        `about.description`では、project READMEを先に読むこと、開発toolをinstallすること、package indexが使えない場合は同梱wheelを使うこと、変更前後でtest suiteを実行することを自然な作業指示として記述します。
        """

        title @= "Configuration"

        configuration_example @= '''
        [about]
        description = """
        This archive contains a Python project prepared for LLM-assisted development.

        Before changing the project:
        1. Read `project/README.md` and the project documentation.
        2. Prepare the development environment with `shikumi`, `shikumi-devdoc`, `basedpyright`, and `ruff`.
        3. If the Python package index is unavailable, install from the bundled `offline_wheels/` directory, for example:
           `python -m pip install --no-index --find-links offline_wheels shikumi shikumi-devdoc basedpyright ruff`
        4. Run the existing test suite before and after modifying the implementation.

        Treat the bundled wheels as an offline installation fallback; use the package index when the environment provides normal network access.
        """

        [always.offline_wheels]
        description = "Offline wheelhouse for the development tools required by this project."
        path = "offline_wheels"
        must = ["*.whl"]

        [case.always.claude]
        description = "The environment can install development tools from the package index, so the offline wheelhouse is not needed."
        exclude = ["offline_wheels"]

        [pluck]
        description = "The Python project to modify and test."
        may = ["*", "*/"]
        ignore = [
            ".git/",
            ".venv/",
            "__pycache__/",
            "*.pyc",
        ]

        [output]
        path = "develop-target.zip"
        overwrite = true
        '''

    class SECTION_004:
        r"""
        package indexを利用できないsandboxではCaseを指定しません。Always Caseなしではeffective Always sourceがすべて参加するため、`offline_wheels/`がArchiveへ入ります。

        ```console
        {{offline_commands}}
        ```

        まずpreviewで内容を確認し、問題なければbuildします。概念的には次のArchiveになります。

        ```text
        develop-target.zip
        ├── README.md
        ├── offline_wheels/
        │   ├── shikumi-0.2.4-py3-none-any.whl
        │   ├── shikumi_devdoc-0.3.5-py3-none-any.whl
        │   ├── basedpyright-1.40.1-py3-none-any.whl
        │   ├── ruff-0.16.10-...whl
        │   └── ...
        └── project/
            └── ...
        ```
        """

        title @= "Offline sandbox: default"

        offline_commands @= """
        dirpluck ./project/ --preview
        dirpluck ./project/
        """

    class SECTION_005:
        r"""
        package indexへ接続できる環境では`.claude` Always Caseを選びます。

        ```console
        {{online_commands}}
        ```

        `.claude`はPluck Caseを選びません。Always Case `claude`だけを選び、`exclude = ["offline_wheels"]`によってprojectの収集ruleを変えずにwheelhouseだけを外します。

        ```text
        develop-target.zip
        ├── README.md
        └── project/
            └── ...
        ```

        provider名をConfigurationに残したくない場合は、同じpatternを`[case.always.online]`のようなcapability-orientedな名前で使えます。
        """

        title @= "Online sandbox: `.claude`"

        online_commands @= """
        dirpluck ./project/ --case .claude --preview
        dirpluck ./project/ --case .claude
        """

    class SECTION_006:
        r"""
        個々の機能の詳細は次を参照してください。

        - [Configuration sources](../configuration/sources.md): Always source。
        - [Configuration selection](../configuration/selection.md): SelectionとAlways Case。
        - [CLI Targets and Cases](../cli/targets.md): `.claude`のようなCase selector。
        - [CLI output](../cli/output.md): `--preview`。
        - [Configuration output](../configuration/output.md): `[output]`。

        このRecipeは完全なgrammar一覧ではなく、一つの具体的workflowを優先して説明しています。厳密な受理grammarとerror条件は[Specification](../specification/INDEX.md)を参照してください。
        """

        title @= "Related documentation"
