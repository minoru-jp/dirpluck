from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title

example_004 = test_target_field("example 004")
example_005 = test_target_field("example 005")


@summary("`.dirpluck-inv` Invocation Template の記述と選択。")
@canonical_source(
    "Invocation Templates",
    filename="invocation-templates.md",
    order=10,
    merge_policy="local",
    heading="title",
)
class CLI_PART:
    r"""この文書は繰り返し使う CLI invocation を `.dirpluck-inv` Invocation Template に保存し、選択・上書きする方法を説明します。

    Template document の厳密な選択と schema は `../specification/document-selection.md`、runtime modifier との組み合わせは `../specification/cli-contract.md` を参照してください。"""

    merge @= TERMS.TERM_1
    merge @= TERMS.TERM_19

    class SECTION_035:
        r"""
        繰り返し使う CLI invocation は、{{TERM_19}}として `.dirpluck-inv` document に保存できます。1 file の `[invocation]` を default Invocation とし、`[invocation.<name>]` に名前付き Invocation entry を追加できます。

        ```toml
        {{example_004}}
        ```

        `config`、`targets`、`case`、`archive_mtime` は default Invocation と各 named entry のどちらでもすべて optional です。Named entry は default Invocation の差分ではなく独立した Invocation で、未指定 field を `[invocation]` から継承しません。`config` / `targets` / `case` / `archive_mtime` は field 名として予約されているため、同名の named Invocation entry は定義できません。`targets` は通常の CLI positional Target reference と同じ grammar をそのまま配列へ保存し、literal list / regular-expression Target selector も使用できます。`config` は `--config PATH` と同じく `.dirpluck` suffix を省略でき、relative path は選択した `.dirpluck-inv` file path の directory を基準に解決します。Template file path や `config` path に symbolic link / Windows directory junction が含まれていても、control document の参照では host OS の通常の filesystem semantics に従います。`config` を省略した場合は runtime cwd の `default.dirpluck`、`targets` を省略した場合は Target なし、`case` を省略した場合は通常の default Case semantics、`archive_mtime` を省略した場合は従来の entry timestamp semantics を使います。

        Template file は `-i PATH` または `--invocation-template PATH` で明示的に選びます。`PATH` は `--config` と同じ filesystem path notation を使い、relative path は runtime cwd、absolute path は host filesystem を基準にします。末尾が `.dirpluck-inv` でなければその suffix を付加します。Invocation Template document path は host OS の通常の filesystem semantics に従って解決し、選択した path の directory が Template 内 relative `config` の基準になります。Invocation Template file 自体に implicit default や別 directory の探索はありません。

        `-e` / `--entry` を省略すると default `[invocation]` を選び、`-e NAME` では `[invocation.NAME]` を選びます。Named entry だけを記述した file でも TOML 上は親 `[invocation]` が成立するため、`-e` なしでは field を持たない default Invocation が選ばれます。完全に空の document は `[invocation]` 自体を持たないため無効です。

        ```console
        {{example_005}}
        ```

        Field を1つも持たない Invocation も有効です。その Invocation は保存済みの実行入力を追加せず、CLI から与えた runtime value と通常の defaults を使います。成功した `--preview` または通常 build では、空の Invocation が選ばれたことを note として CLI output に表示します。これは warning ではなく、Always-only build や source 0件の README-only build などが正当に成立し得る状態です。

        Invocation Template は保存済み invocation を一般的に差分合成する仕組みではありません。`-i` / `--invocation-template` と positional `TARGET`、`--config` は組み合わせません。`--case CASE` は選択した Invocation の `case` を実行時に上書きでき、`--archive-mtime VALUE` は Invocation の `archive_mtime` を上書きできます。`--here` / `--output` / `--force`、`--preview`、`--sequence`、`--archive-mtime`、`--paths` も、それぞれ通常の組み合わせ制約に従う runtime modifier として使用できます。`-e` / `--entry` は `-i` / `--invocation-template` と一緒にだけ使用できます。

        `.dirpluck-inv` は Configuration ではなく、`about.base` の参照先にもなりません。選択した Invocation の Configuration / Target / Case / Archive mtime 解決後は通常の dirpluck execution と同じ semantics を使います。
        """

        title @= "Invocation Template"

        example_004 @= """
        [invocation]
        config = "release"
        targets = ["work/frontend/", "work/backend/"]

        [invocation.docs]
        config = "release"
        targets = ["docs/"]
        case = "publish"
        archive_mtime = "zip-epoch"
        """

        example_005 @= """
        dirpluck -i release
        dirpluck -i release -e docs
        dirpluck -i invocations/release --entry docs --case audit
        dirpluck --invocation-template ../shared/release --preview
        """

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_19
