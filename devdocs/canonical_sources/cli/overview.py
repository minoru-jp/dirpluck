from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_001 = test_target_field("example 001")
example_002 = test_target_field("example 002")
example_003 = test_target_field("example 003")
example_017 = test_target_field("example 017")


@summary("CLI の基本形、Configuration 選択、help、終了 status。")
@canonical_source(
    "CLI overview", filename="overview.md", order=0, merge_policy="local", heading="title"
)
class CLI_PART:
    r"""この文書は `dirpluck` CLI の基本的な呼び出し方、Configuration の選択、help / version、終了 status を説明します。

    Target / Case は `targets.md`、Invocation Template は `invocation-templates.md`、preview と Output runtime option は `output.md` を参照してください。厳密な document selection は `../specification/document-selection.md`、CLI option の組み合わせと終了契約は `../specification/cli-contract.md` に定義されています。"""

    merge @= TERMS.TERM_1

    class SECTION_002:
        r"""
        ```text
        {{example_001}}
        ```

        選択した{{TERM_15}}で fixed source が1個以上参加する場合、Pluck も定義されている Configuration でも `TARGET` reference を省略し、Always source と選択した Always Case で有効化された Extra source だけを Archive にできます。Target を指定した場合は従来どおり Pluck を directory Target に適用します。Pluck がなくても `target_kind = "file"` / `"both"` の Scope から file Target は positional argument で選択できます。Directory Target は Pluck を必要とします。

        ```console
        {{example_002}}
        ```

        Target reference は literal reference、Scope expansion、Target selector を使えます。Literal reference は末尾 `/` なしを file、末尾 `/` ありを directory とし、default Scope の directory は `./NAME/`、named Scope では `SCOPE/NAME/` と書きます。`/` / `SCOPE/` は Scope expansion、`:[...]` / `SCOPE:[...]` は typed literal list selector、`:<...>` / `SCOPE:<...>` は regular-expression selector です。どの形式も{{TERM_16}}から{{TERM_3}}を選びます。
        """

        title @= "基本形"

        example_001 @= """
        dirpluck [TARGET ...] [--config PATH] [--case CASE] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
        dirpluck -i PATH [-e NAME] [--case CASE] [--here[=FILENAME] | --output PATH] [--force] [--sequence N] [--archive-mtime VALUE] [--preview] [--paths]
        dirpluck --version
        """

        example_002 @= """
        dirpluck ./example/
        dirpluck work/project-a/ work/project-b/
        dirpluck --config snapshot
        """

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_3
        merge @= TERMS.TERM_15
        merge @= TERMS.TERM_16

    class SECTION_003:
        r"""
        Configuration document は TOML syntax を使用しますが、filename extension は `.dirpluck` です。`--config` を省略した場合だけ、runtime cwd の `default.dirpluck` を自動的に使用します。これは CLI が暗黙に探す唯一の Configuration です。

        別の Configuration は `--config PATH` で明示します。`PATH` は filesystem location と同じ `/` separator の表記を使い、relative path は runtime cwd、absolute path は host filesystem を基準にします。末尾が `.dirpluck` でなければ suffix を付加するため、dot を含む document name もそのまま使えます。Windows でも CLI path separator には `\` ではなく `/` を使います。

        ```console
        {{example_003}}
        ```

        `--config` を指定した場合は、その path が表す1個の Configuration document だけを使用し、別 directory の同名 file を探索しません。Directory 自体を指定してその中の `default.dirpluck` を補うこともありません。Configuration document path は host OS の通常の filesystem semantics に従って解決し、symbolic link / Windows directory junction を含む path も control document の選択では特別に拒否しません。dirpluck は選択した path の absolute な表記を document location として保持し、その document 内の relative path はその location の directory を基準にします。dirpluck は file 内容から Configuration らしさを推論したり、任意の `*.dirpluck` file を自動選択・列挙したりしません。`.toml` file を Configuration として扱う互換 fallback もありません。

        Output は `--preview` には不要です。通常 build では root Configuration 自身の Output declaration、または CLI の runtime Output (`--here` / `--output`) のどちらかを使います。Configuration が `about.base` で参照する Base Configuration は CLI の自動選択対象ではありません。
        """

        title @= "Configuration を選ぶ"

        example_003 @= """
        dirpluck ./example/ --config review
        dirpluck ./example/ --config configs/release-1.2
        dirpluck ./example/ --config ../shared/review.dirpluck
        """

        merge @= TERMS.TERM_1

    class SECTION_008:
        r"""
        ```console
        {{example_017}}
        ```
        """

        title @= "Help と version"

        example_017 @= """
        dirpluck --help
        dirpluck --version
        """

        merge @= TERMS.TERM_1

    class SECTION_009:
        r"""
        正常終了は status 0 です。CLI argument error や dirpluck の validation / build error は status 2 で終了し、`dirpluck: error:` に続けて理由を表示します。

        Archive を生成する通常実行では、成功すると output path を標準出力へ表示します。Selection traversal で symbolic link / Windows directory junction として認識した entry を除外していた場合は、除外件数も informational note として表示します。この runtime note は Archive 内の README には書き込みません。
        """

        title @= "終了とエラー"
