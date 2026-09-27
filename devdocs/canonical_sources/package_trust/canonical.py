from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.norms.common import canonical_source, merge
from shikumi_devdoc.norms.document import title


@canonical_source('dirpluck Trust Quick Reference', filename='TRUST.md', placeholders=False, heading="title")
class SECTION_001:
    r"""
    この文書は installed package に同梱する compact trust reference です。完全な trust model は同じ release の source distribution にある `docs/TRUST.md`、厳密な互換性契約は `docs/specification/INDEX.md` を参照してください。
    """

    merge @= TERMS.TERM_1

    class SECTION_002:
        r"""
        {{TERM_2}}と{{TERM_19}}はどちらも実行指示です。第三者から受け取った document は、実行前に参照する Configuration、Target、Case、Scope / Always source、Selection、Output を確認してください。{{TERM_1}}は、参照先が機密か、description が実態と一致するか、宣言された操作が利用者の目的に対して安全かを推論しません。
        """
        title @= 'Configuration と Invocation Template'

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_2
        merge @= TERMS.TERM_19

    class SECTION_003:
        r"""
        {{TERM_1}}は実行 user の OS permission を越えて読み書きしません。一方、user がアクセスでき、Configuration の path rule で参照できる relative `..` や absolute path は source / Output に指定できます。

        Configuration / Invocation Template document と明示した Scope / Always root location は host OS の通常の filesystem semantics で解決します。明示 root の内側を自動 traversal するときは、認識した symbolic link / Windows directory junction をたどらず Archive に含めません。FIFO、socket、device など regular file / regular directory でない entry も Archive 対象外です。未知の platform-specific mechanism を完全に列挙・保証するものではありません。
        """
        title @= 'Filesystem boundary'

        merge @= TERMS.TERM_1

    class SECTION_004:
        r"""
        Hidden file、repository metadata、environment file、key material などを filename や内容から推論して自動 ignore しません。外部へ渡す Archive では `must` / `may` / `ignore` と実際の生成内容を用途に応じて確認してください。

        `--preview` は Archive を書き込まず archive-relative contents plan を確認できます。認識した non-ignored link-like entry を traversal から除外した場合は件数も表示します。
        """
        title @= 'Selection と preview'


    class SECTION_005:
        r"""
        Output は Configuration または runtime option が宣言した destination と overwrite policy に従います。{{TERM_1}}は同じ output path を使う複数 process の lock や競合調停を提供しません。

        生成される{{TERM_10}}は source filesystem path を既定では記録しませんが、`--paths` を使うと absolute path など local environment の情報を含み得ます。README から path を隠すことは Archive contents の inspection / sanitization ではありません。
        """
        title @= 'Output と共有'

        merge @= TERMS.TERM_1
        merge @= TERMS.TERM_10
