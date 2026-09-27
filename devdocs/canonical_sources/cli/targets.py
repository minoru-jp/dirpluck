from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_006 = test_target_field("example 006")
example_007 = test_target_field("example 007")
example_008 = test_target_field("example 008")
example_009 = test_target_field("example 009")
example_010 = test_target_field("example 010")


@summary('Target reference、Scope expansion、Case の CLI 操作。')


@canonical_source('Targets and Cases', filename='targets.md', order=20, placeholders=False, heading="title")
class CLI_PART:
    r"""この文書は positional Target reference、Scope expansion、Case selection を CLI から指定する方法を説明します。

    Scope / Namespace の authoring は `../configuration/sources.md`、Case の authoring は `../configuration/selection.md`、厳密な Target / Case semantics は `../specification/runtime-targets.md` に定義されています。"""

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_3
    merge @= TERMS.TERM_4
    merge @= TERMS.TERM_16

    class SECTION_004:
        r"""
        Pluck がある Configuration では、各 positional `TARGET` から解決した source directory へ同じ Pluck selection が独立して適用されます。

        常設の default Scope から1 Target を選ぶ場合は directory name だけを指定します。Default Scope は常に root Configuration file の directory を root とします。Configuration を別 directory に置けば default Scope もその directory に移るため、別の Target root が必要な場合は named Scope を定義します。

        ```console
        {{example_006}}
        ```

        名前付き Scope から選ぶ場合は `<scope>/<name>` を使います。

        ```console
        {{example_007}}
        ```

        `work/acme` は `work` Scope 直下の `acme` だけを Target とします。`work` Scope が未定義なら error で、別の relative path interpretation へ fallback しません。

        Scope 直下の eligible directory をすべて Target にするには、次の expansion form を使います。

        ```console
        {{example_008}}
        ```

        `/` は default Scope、`work/` は named Scope `work` を全展開します。`/` は filesystem root ではありません。どちらも direct child directory だけを展開し、再帰列挙しません。Scope の `ignore` に一致する directory は Target candidate から除きます。未使用の named Scope の path が現在存在しなくても、別の Scope だけを使う実行は失敗しません。

        `./`、`./acme`、`/acme`、`work/team/acme`、absolute filesystem path は Target reference として受理しません。

        Pluck がない Configuration は Always source など固定 source だけで実行できます。

        ```console
        {{example_009}}
        ```

        Scope と `ignore` の定義方法は `configuration/INDEX.md`、Target reference、boundary、archive path の厳密な規則は `specification/INDEX.md` を参照してください。
        """
        title @= 'Target の指定'

        example_006 @= "dirpluck acme contoso"

        example_007 @= "dirpluck work/acme"

        example_008 @= """
        dirpluck /
        dirpluck work/
        """

        example_009 @= "dirpluck --config project-snapshot"

        merge @= TERMS.TERM_1

    class SECTION_005:
        r"""
        名前付き{{TERM_4}}を選ぶには `--case NAME` を使います。

        ```console
        {{example_010}}
        ```

        1回の実行で指定する Case は1個です。Pluck と Always source が Case をどう選ぶかは `specification/INDEX.md` に定義しています。
        """
        title @= 'Case'

        example_010 @= "dirpluck acme --case audit"

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_4
