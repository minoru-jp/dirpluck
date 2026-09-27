from devdocs.canonical_sources.vocabulary.canonical import TERMS
from devdocs.canonical_sources.specification.composition import SPECIFICATION_PART as COMPOSITION_SPEC
from shikumi_devdoc.fields.specification import MUST, MUST_NOT, condition, level, related
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import title


@summary('Selection、Shared pattern、include/ignore pattern grammar。')


@canonical_source('Selection and shared patterns', filename='selection.md', order=70, placeholders=False, heading="identity")
class SPECIFICATION_PART:
    class SPEC_065:
        r"""Pluck / Always source の base または Case selection は、`must` / `may` の candidate を少なくとも1個必要とする。Candidate は direct pattern または Shared reference で記述できる。`description` は任意で、記述する場合だけ空でない string を必要とする。"""
        level @= MUST

    class SPEC_066:
        r"""
        `must` / `may` の array item は direct pattern string または1要素 Shared reference array とする。

        ```text
        "foo"       direct pattern
        ["foo"]     Shared reference
        ```
        """
        level @= MUST

    class SPEC_067:
        r"""
        `ignore` の direct string は name pattern とする。1要素 nested array は reference marker とし、中の string が `./` で始まれば Selection-relative path reference、それ以外なら `shared.ignore` の Shared reference とする。

        ```text
        "*.pyc"                         direct name pattern
        ["python-noise"]               Shared ignore reference
        ["./tests/fixtures/big.bin"]   file path reference
        ["./tests/fixtures/"]          directory path reference
        ```
        """
        level @= MUST

    class SPEC_068:
        r"""Nested array の要素数はちょうど1、要素は non-empty string でなければならない。`[]`、`["foo", "bar"]`、`[123]` は error とする。`must` / `may` では nested array は Shared reference 専用とする。"""
        level @= MUST

    class SPEC_069:
        r"""
        Shared reference namespace は field から一意に決まる。

        ```text
        must   -> shared.must
        may    -> shared.may
        ignore -> shared.ignore
        ```
        """
        level @= MUST

    class SPEC_070:
        r"""Shared pattern definition の value は direct pattern の non-empty array とし、Shared reference や path reference を nested させない。"""
        level @= MUST

    class SPEC_071:
        r"""Base composition 後の effective shared namespace に対して Shared reference を解決する。Unknown reference は Configuration error とする。Selection array の順序を保って Shared reference をその pattern set へ展開する。Path reference は Shared namespace を参照せず、その Selection の source root を基準に解釈する。"""
        level @= MUST
        related @= (COMPOSITION_SPEC.SECTION_402.SPEC_034,)

    class SPEC_072:
        r"""展開後の `must` 内、`may` 内、`ignore` 内の同一記述の duplicate pattern/reference、および `must` / `may` 間の duplicate include pattern は Configuration error とする。一方、異なる ignore 条件が同じ filesystem entry に一致する semantic overlap は有効で、除外結果は条件の和とする。"""
        level @= MUST

    class SPEC_073:
        r"""`allow_empty` は boolean で既定 `false` とする。`allow_empty = true` は、Shared reference 展開後に `must` pattern を持たない selection だけで指定できる。"""
        level @= MUST
        condition @= "`allow_empty = true` を指定する場合"

    class SECTION_601:
        title @= 'Include pattern grammar (`must` / `may`)'

        class SPEC_074:
            r"""`must` と `may` の direct / expanded pattern は source directory からの `/` separator の relative path とする。Absolute path、`.` / `..` による逸脱、backslash を拒否する。"""
            level @= MUST

        class SPEC_075:
            r"""
            各 path element には `*` を最大1個だけ含められる。`*` はひとつの実体名内部で0文字以上に一致し、path separator を越えない。そのため Configuration に書いた path hierarchy の深さは固定される。

            ```text
            src
            README.md
            dist/package-*.whl
            packages/*/dist/package-*.whl
            ```
            """
            level @= MUST

        class SPEC_076:
            r"""`must` pattern は1件以上の **non-ignored selectable entry** に一致しなければ error、`may` pattern は0件一致を許容する。複数一致した場合は `ignore` 適用後に残ったものを selection candidate とする。"""
            level @= MUST
            condition @= "`must` / `may` pattern を評価する場合"

        class SPEC_077:
            r"""最後に一致した実体が regular file ならその file を選択し、regular directory なら `ignore` に従って配下の regular file を再帰収集する。`ignore` は entry の種類による診断より優先し、ignored entry は selectable match、link-only / special-entry-only match、skipped-link count のいずれにも含めない。Symbolic link または Windows directory junction として認識した **non-ignored** entry は selectable entry とみなさない。Pattern がそのような non-ignored link-like entry だけに一致した場合、`must` は通常の不存在と区別できる理由付き error とし、`may` は optional missing として扱う。"""
            level @= MUST
            condition @= "include pattern が link-like entry に一致する場合"

        class SPEC_078:
            r"""FIFO、socket、device など regular file / regular directory ではない **non-ignored** filesystem entry も selectable entry とせず、Archive に含めない。`may` がそのような特殊 entry に一致しても選択せず optional missing とし、`must` が特殊 entry だけに一致した場合は unsupported special filesystem entry にしか一致しなかったことを示す理由付き error とする。Regular directory の配下を再帰収集するときに現れる特殊 entry は traversal せず、静かに除外する。内容や filename の意味に基づく暗黙 ignore は行わない。"""
            level @= MUST_NOT
            condition @= "include pattern が special filesystem entry に一致する場合"

        class SPEC_079:
            r"""Matching は OS に依存せず case-sensitive とする。`**`、`?`、character class (`[]`)、`!` はサポートしない。複数一致を version、mtime、その他 metadata で順位付けしない。"""
            level @= MUST

    class SECTION_602:
        title @= 'Ignore grammar'

        class SPEC_080:
            r"""Selection の `ignore` は name pattern と Selection-relative concrete path reference の2種類を持つ。"""
            level @= MUST

        class SPEC_081:
            r"""
            Direct string はひとつの実体名を case-sensitive に照合する。末尾 `/` の pattern は directory name、`/` のない pattern は file name に適用する。対応形式は次とする。

            ```text
            name      exact
            name*     prefix
            *name     suffix
            *name*    substring
            ```
            """
            level @= MUST

        class SPEC_082:
            r"""
            Directory name pattern ではこの body の末尾に `/` を付ける。

            ```text
            .git/
            __pycache__/
            tmp-*/
            ```
            """
            level @= MUST

        class SPEC_083:
            r"""
            Selection-relative path reference は1要素 nested arrayの stringを `./` で始める。Pluck では Target directory、Always source では解決済み Always source directory を Selection root とする。末尾 `/` は concrete directory path、末尾 `/` なしは concrete file path とし、filesystem 上の現状から file / directory を推測しない。

            ```text
            ["./tests/fixtures/big.bin"]   exact file path
            ["./tests/fixtures/"]          exact directory path and its subtree
            ```
            """
            level @= MUST

        class SPEC_084:
            r"""Path reference は Selection root の内側だけを指し、`./` 自体、`..` component、absolute path、glob、backslash を拒否する。Path separator は `/` とする。Directory path reference に一致した directory は subtree を traversal する前に prune する。File path reference は完全一致した fileだけを除外する。"""
            level @= MUST

        class SPEC_085:
            r"""Name pattern、Shared ignore expansion、path reference は集合的な除外条件として適用する。同じ entry に複数条件が一致しても error ではなく、評価順序は observable semantics に含めない。実装は directory 条件に一致した subtree を早期に prune してよい。"""
            level @= MUST

        class SPEC_086:
            r"""`ignore` は link-like / special entry の種類による診断より優先する。Ignored entry は Selection candidate、link-only / special-entry-only error の根拠、skipped-link count の対象にせず、ignored subtree の entry も列挙や traversal-time validation の対象にしない。末尾 `/` のない name pattern は regular file だけでなく、同じ name を持つ特殊 entry にも適用する。Path reference が link-like entry 自身に一致する場合も ignored entry として扱う。"""
            level @= MUST

        class SPEC_087:
            r"""Name pattern では `*` 単体、`*/`、`foo*bar` のような internal wildcard、`**`、`?`、character class、`!`、backslash、body 内の path separator を拒否する。Path reference は wildcard syntax を持たない。"""
            level @= MUST_NOT
