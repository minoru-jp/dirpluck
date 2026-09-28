from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge
from shikumi_devdoc.norms.document import test_target_field, title


configuration_example = test_target_field("configuration example")
workspace_example = test_target_field("workspace example")
preview_command = test_target_field("preview command")
preview_output = test_target_field("preview output")
build_command = test_target_field("build command")
archive_readme = test_target_field("archive README")


@canonical_source('Getting started with dirpluck', filename='GETTING_STARTED.md', merge_policy="local", heading="title")
class SECTION_001:
    r"""
    この文書では、最小構成から {{TERM_1}} を試し、preview で内容を確認してから Archive を生成するまでを通して説明します。

    Configuration field の詳細は `configuration/INDEX.md`、CLI option と Invocation Template は `cli/INDEX.md`、trust boundary は `TRUST.md` を参照してください。
    """

    merge @= TERMS.TERM_1

    class SECTION_002:
        r"""
        `--config` を指定しない場合、{{TERM_1}} は runtime cwd の `default.dirpluck` を使用します。まずは次の内容を `default.dirpluck` として保存します。

        ```toml
        {{configuration_example}}
        ```

        `pluck` は実行時に選ぶ Target から収集する内容、`always.guidelines` は毎回一緒に収集する固定 source、`output` は生成先を定義しています。
        """
        title @= '1. Configuration を作る'

        configuration_example @= """
        [about]
        description = "Review package for the example project."

        [pluck]
        description = "Project files selected for review."
        must = ["README.md", "src/", "tests/"]
        ignore = [".git/", "__pycache__/", "*.pyc"]

        [always.guidelines]
        path = "review-guidelines"
        description = "Review guidelines shared across projects."
        must = ["*.md"]

        [output]
        path = "review.zip"
        """

        merge @= TERMS.TERM_1

    class SECTION_003:
        r"""
        同じ directory に、たとえば次の file があるとします。

        ```text
        {{workspace_example}}
        ```

        `example/` が実行時に選ぶ {{TERM_3}}、`review-guidelines/` が Configuration に固定した Always source です。
        """
        title @= '2. 対象を用意する'

        workspace_example @= """
        .
        ├── default.dirpluck
        ├── example/
        │   ├── README.md
        │   ├── src/
        │   │   └── main.py
        │   └── tests/
        │       └── test_main.py
        └── review-guidelines/
            └── review.md
        """

        merge @= TERMS.TERM_3

    class SECTION_004:
        r"""
        Archive を書き込む前に `--preview` で contents plan を確認します。

        ```console
        {{preview_command}}
        ```

        この例では次のように表示されます。

        ```text
        {{preview_output}}
        ```

        先頭の `README.md` は、{{TERM_1}} が Archive の内容を説明するために生成する file です。
        """
        title @= '3. Preview で確認する'

        preview_command @= "dirpluck ./example/ --preview"
        preview_output @= """
        ├── README.md
        ├── example/
        │   ├── README.md
        │   ├── src/
        │   │   └── main.py
        │   └── tests/
        │       └── test_main.py
        └── review-guidelines/
            └── review.md
        """

        merge @= TERMS.TERM_1

    class SECTION_005:
        r"""
        Preview に問題がなければ、同じ Target で Archive を作成します。

        ```console
        {{build_command}}
        ```

        `[output]` に従って `review.zip` が作成され、preview で確認した file と生成された `README.md` が入ります。この例の Archive README は次の内容です。

        ```markdown
        {{archive_readme}}
        ```
        """
        title @= '4. Archive を作る'

        build_command @= "dirpluck ./example/"
        archive_readme @= """
        # Archive contents

        Review package for the example project.

        ## `example/`

        Files: 3

        Project files selected for review.

        ## `review-guidelines/`

        Files: 1

        Review guidelines shared across projects.
        """

    class SECTION_006:
        r"""
        Configuration の `description` は抽出意味論を変えず、生成される Archive README に人間向けの context を追加します。Scope、Namespace、Case、Shared patterns、Base Configuration、Output の詳細は `configuration/INDEX.md` に分けています。

        同じ Configuration / Target / Case の組み合わせを繰り返す場合は `.dirpluck-inv` Invocation Template に呼び出しを保存できます。詳しくは `cli/INDEX.md` を参照してください。

        外部へ渡す Archive を扱う場合は、広い selection や機密 file の扱いを `TRUST.md` で確認してください。
        """
        title @= '次に読む'

