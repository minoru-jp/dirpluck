"""dirpluck project status canonical source."""

from shikumi_devdoc.norms.common import canonical_source
from shikumi_devdoc.norms.document import title


@canonical_source("dirpluck プロジェクトステータス", filename="STATUS.md", heading="title")
class STATUS:
    """
    dirpluck の現在の開発段階、互換性方針、および 1.0 へ向けた判断基準を示します。

    0.18.x は **Beta** 系列です。0.9.0 で Configuration language と filesystem model の大きな再編を行い、0.10.0 以降は公開面の互換性維持を強く志向してきました。しかし、その後の実運用から 1.0 前に修正すべき設計上の問題がまだ残っていることが確認されたため、0.16.0 で残りの 0.x series の互換性方針を見直しました。
    """

    class CURRENT_STATUS:
        """
        現在の公開 version 系列は `0.18.x`、開発段階は **Beta** です。

        残りの 0.x series は、1.0.0 の公開契約を確定するための設計収束期間として扱います。既存利用者への移行負担は抑えますが、1.0 に不適切な設計を互換性のためだけに固定することはしません。

        0.15.0 は公開せず、そこで予定していた契約変更は 0.16.0 に統合しました。0.16.0 では内部実行 model を、入力の parse / normalize、filesystem からの extract、Archive / message output の3段階へ再構成しています。0.17.0 の Layout / conditional description と、0.18.0 の Extra source もこの境界に沿って追加しています。公開 grammar を後段で再解釈せず、各層が前段の入力言語や後段の出力形式を必要以上に知覚しない依存方向を 1.0 向けの内部基盤とします。
        """

        title @= "現在のステータス"

    class STABILITY_POLICY:
        """
        0.10.0 以降は、公開された Configuration language、CLI、公式 Python API、Archive semantics の破壊的変更を原則として避ける方針を採っていました。0.13.0 の entry-type redesign や 0.16.0 の Always Archive identity redesign を含む実運用上の発見から、1.0 前に中核設計をさらに修正する必要があることが明確になったため、この方針は 0.16.0 で取り下げます。

        0.16.0 から 1.0.0 直前までの 0.x release では、正確性、安全性、予測可能性、設計整合性、または 1.0 の長期的な公開契約のために必要であれば Breaking Change を行います。Breaking Change 自体を避けることを最優先にはしません。

        一方で、Breaking Change を無言で導入することもしません。技術的に有効な場合は deprecation period、migration warning、Migration Guide、明示的な before / after を提供し、自動検出できる旧用法や出力変更は CLI と公式 Python API の双方から確認できる形で通知します。移行支援のためだけに旧設計を恒久的な互換 mode として残すことはしません。

        Generated Archive README、診断 message など、人間が読むことを主目的とした生成出力の exact wording / formatting は安定した machine-readable interface とはみなしません。可読性や明瞭性の改善に伴い、これらの書式や文言は今後の release でも変更する場合があります。Programmatic integration は Configuration、CLI、公式 Python API、Archive semantics など明示された公開契約に依存させてください。

        内部 module、repository-local development tools、文書生成 workspace はこの互換性方針の対象外です。
        """

        title @= "安定性方針"

    class BETA_GOALS:
        """
        Beta 期間では、特に次の点を確認します。

        - 実際の project tree と共有用 Archive 作成で、Configuration model の責務境界が明確で継続利用できること。
        - CLI と公式 Python API が同じ invocation semantics と migration diagnostics を提供できること。
        - Scope、Selection、Base、Layout、Namespace、Always、Extra、Output、Archive planning の主要契約を 1.0 向けに収束させること。
        - parse / normalize → extract → output の責務境界を維持し、入力 language の概念や presentation 都合が不要な層へ逆流しないこと。
        - 実運用で見つかった不自然な意味境界を、必要なら Breaking Change を含めて 1.0 前に修正すること。
        - 変更時に deprecation、warning、Migration Guide など適切な移行手段を提供できること。
        - 文書、診断、platform compatibility など利用体験上の改善を継続できること。
        """

        title @= "Beta 期間の目的"

    class PATH_TO_ONE:
        """
        1.0.0 は、0.x で必要な設計修正と移行を終え、Configuration、CLI、公式 Python API、filesystem / Archive model を安定した公開契約として固定できると判断した時点でリリースします。

        1.0 への移行条件は機能を際限なく追加することではありません。既知の中核的な設計問題を 0.x のまま持ち越さず、Breaking Change を前提とした migration warning や pre-1.0 compatibility semantics も整理したうえで、以後の互換性維持を強く約束できる状態にすることを重視します。
        """

        title @= "1.0 への移行"

    class DOCUMENTATION_TOOLING:
        """
        公開文書の canonical source / canonical document pipeline には `shikumi-devdoc>=0.3.2` を使用します。これは repository development 用 dependency であり、dirpluck の runtime dependency ではありません。

        公開 source repository で canonical document を再生成する際は、必要な Shikumi 0.2.0 と shikumi-devdoc 0.3.2 が公開済みであることを前提とします。文書生成対象、出力先、project context など dirpluck 固有の orchestration は `tools/render_canonical_docs.py` に保持し、shikumi-devdoc の汎用 API へ project 固有情報を押し込みません。
        """

        title @= "文書生成基盤"

    class DISTRIBUTION_NOTE:
        """
        dirpluck は PyPI で package を公開し、source repository は [https://github.com/minoru-jp/dirpluck](https://github.com/minoru-jp/dirpluck) で公開します。

        PyPI の project description からも文書へ移動できるよう、root README の公開文書 link は GitHub の `main` branch 上にある対応 file の URL を使用します。Package metadata の project URLs も同じ公開 repository を基準にし、Homepage、Documentation、Repository、Issues、Changelog への入口を提供します。

        Wheel には引き続き同じ release の README、Glossary、CLI / Configuration / Python API guide、Trust model、Specification、CHANGELOG、STATUS を `dirpluck/_docs/` 以下へ同梱します。Installed wheel 内の文書は network access を前提としません。
        """

        title @= "配布上の留意点"
