from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_006 = test_target_field("example 006")
example_007 = test_target_field("example 007")
example_008 = test_target_field("example 008")
example_009 = test_target_field("example 009")
example_010 = test_target_field("example 010")
example_011 = test_target_field("example 011")
example_012 = test_target_field("example 012")


@summary("Target reference、Scope expansion、Case の CLI 操作。")
@canonical_source(
    "Targets and Cases", filename="targets.md", order=20, merge_policy="local", heading="title"
)
class CLI_PART:
    r"""この文書は positional Target reference、Scope expansion、Case selection を CLI から指定する方法を説明します。

    Scope / Namespace の authoring は `../configuration/sources.md`、Case の authoring は `../configuration/selection.md`、厳密な Target / Case semantics は `../specification/runtime-targets.md` に定義されています。"""

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_3
    merge @= TERMS.TERM_4
    merge @= TERMS.TERM_16

    class SECTION_004:
        r"""
        Positional `TARGET` は Scope の `target_kind` に応じて directory、regular file、またはその両方から解決します。Directory Target には effective Pluck selection を独立して適用し、file Target はその file 自体を atomic source として収録します。

        Literal Target reference は記法だけで entry type を決めます。末尾 `/` なしは file、末尾 `/` ありは directory で、filesystem の実体型から意味を推測しません。Default Scope では `NAME` / `./NAME` が file、`./NAME/` が directory です。`NAME/` は named Scope expansion と同じ形になるため、default Scope の directory では `./` を明示します。Default Scope は常に root Configuration file の directory を root とします。

        ```console
        {{example_006}}
        ```

        名前付き Scope では `<scope>/<name>` が file、`<scope>/<name>/` が directory です。

        ```console
        {{example_007}}
        ```

        `work/acme/` は `work` Scope 直下の directory `acme/` だけを Target とします。`work` Scope が未定義なら error で、別の relative path interpretation へ fallback しません。Syntax が要求する型を Scope の `target_kind` が許可しない場合も error です。Literal Target が要求した型と同名の実体型が異なる場合、error diagnostic は末尾 `/` の追加または削除を案内します。

        Scope 直下の eligible Target candidate をすべて選ぶには、次の expansion form を使います。

        ```console
        {{example_008}}
        ```

        `/` は default Scope、`work/` は named Scope `work` を全展開します。`/` は filesystem root ではありません。`target_kind = "directory"` では direct child directory、`target_kind = "file"` では direct child regular file、`target_kind = "both"` ではその両方を展開し、再帰列挙しません。Scope の `ignore` に一致する candidate は除外します。未使用の named Scope の path が現在存在しなくても、別の Scope だけを使う実行は失敗しません。

        Target selector はすべての `target_kind` で使えます。`[...]` は typed literal Target list です。Item は末尾 `/` なしなら file、末尾 `/` ありなら directory です。`/` は item separatorにも使うため、途中の directory itemでは `NAME//NEXT` のように2連になります。3連以上は error です。最初の `[` と最後の `]` だけが外郭syntaxで、内部の `[` / `]` などは Target name の通常文字として扱います。

        ```console
        {{example_011}}
        ```

        `<...>` は regular-expression selector です。Eligible direct-child file は `NAME`、directory は `NAME/` と正規化し、その文字列全体へ Python-compatible regular expression を full-match します。したがって `<repo>` は file、`<repo/>` は directory、`<repo/?>` は両方を明示できます。Pattern は空にできず、512 character 以下です。Invalid regular expression と0件 match は error です。`/` を含めても再帰探索にはならず、candidate は Scope 直下だけです。

        この regular-expression Target selector は、Selection の通常 string pattern とは別の役割です。Selection の通常 string は directory tree の予測可能な traversal / name exclusion を制御し、必要なら `{ match = "..." }` で root-relative path 全体へ regular expression を使えます。一方、`<...>` Target selector は eligible な direct-child Target の normalized name の追加絞り込みだけを行います。Selection 側の pattern と structured `match` は `../configuration/selection.md` を参照してください。

        ```console
        {{example_012}}
        ```

        Default Scope では `:[file-a/dir-b/]` / `:<regex>`、named Scope では `work:[file-a/dir-b/]` / `work:<regex>` のように書きます。Selector は `target_kind = "directory"` / `"file"` / `"both"` のすべてで使用でき、Scope の type filter、`ignore`、link-like exclusion で eligible Target を決めてから適用します。`both` で selector が file と directory の両方を解決した場合も、directory にだけ Pluck を適用し、file は atomic source とします。

        Shell から使用する場合、`[]`、`<>`、regular-expression metacharacter が shell 自身に解釈されないよう、selector reference 全体を quote してください。

        `./` 単独、`/acme`、`work/team/acme`、absolute filesystem path は Target reference として受理しません。`./acme` と `./acme/` はそれぞれ default Scope の file / directory Target を明示する有効な形式です。

        Target reference は0個でも実行できます。Targetを指定しないrunでは Pluck は source selection に使用せず、通常参加する Always source と、選択した Always Case の `include` / `add` で有効化された Extra source があれば、それら fixed source だけを抽出します。参加する fixed source もなければ source 0件の正常な run となり、生成するArchiveは `README.md` だけを含みます。Pluck がない Configuration でも file-capable Scope (`target_kind = "file"` / `"both"`) から file Target は選べます。Directory Target は Pluck を必要とします。

        ```console
        {{example_009}}
        ```

        Scope と `ignore` の定義方法は `configuration/INDEX.md`、Target reference、boundary、archive path の厳密な規則は `specification/INDEX.md` を参照してください。
        """

        title @= "Target の指定"

        example_006 @= "dirpluck ./acme/ ./contoso/"

        example_007 @= "dirpluck work/acme/"

        example_008 @= """
        dirpluck /
        dirpluck work/
        """

        example_009 @= "dirpluck --config project-snapshot"

        example_011 @= "dirpluck 'work:[repo-a//repo-b.zip]'"

        example_012 @= r"dirpluck 'work:<repo-.*/?>'"

        merge @= TERMS.TERM_1

    class SECTION_005:
        r"""
        名前付き{{TERM_4}}は `--case CASE` で選びます。Case selector は Pluck と Always の2軸です。Always Case は Always source の参加選択と Extra source の有効化を行います。`PLUCK` は Pluck Case だけ、`.ALWAYS` は Always Case だけ、`PLUCK.ALWAYS` は両方を指定します。

        ```console
        {{example_010}}
        ```

        2軸は独立して検証します。定義済み Case の適用結果として source が0件でも正常です。Pluck Case と Always Case の Configuration semantics は `specification/INDEX.md` に定義しています。
        """

        title @= "Case"

        example_010 @= """
        dirpluck ./acme/ --case audit
        dirpluck --case .release
        dirpluck ./acme/ --case audit.release
        """

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_4
