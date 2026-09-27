<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/status/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `devdocs/canonical_documents/` にある日本語 canonical document はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの canonical document を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や canonical document を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck プロジェクトステータス

dirpluck の現在の開発段階、互換性方針、および 1.0 へ向けた判断基準を示します。

0.11.x は **Beta** 系列です。0.9.0 で Configuration language と filesystem model の大きな再編を行い、0.10.0 では runtime Output と公開文書体系を現在の設計へ揃えました。以後はこの公開面を実運用で検証しながら、互換性を積極的に維持します。

## 現在のステータス

現在の公開 version 系列は `0.11.x`、開発段階は **Beta** です。

Beta 期間は公開 interface を自由に作り直すための期間ではありません。Configuration、CLI、公式 Python API、Archive semantics を現在の設計で継続利用できることを実運用の中で確認し、必要な改善を可能な限り additive に行います。

## 安定性方針

0.10.0 以降、公開された Configuration language、CLI、公式 Python API、Archive semantics の破壊的変更は重大な理由がある場合を除いて行いません。

重大な理由には、維持することで正確性・安全性・中核的な設計整合性を損なう欠陥などが含まれます。通常の機能追加や改善は additive に行い、既存 interface を置き換える必要が生じた場合は、可能な限り deprecation と移行期間を設けます。

一方、generated Archive README、診断 message など、人間が読むことを主目的とした生成出力の exact wording / formatting は安定した machine-readable interface とはみなしません。可読性や明瞭性の改善に伴い、これらの書式や文言は今後の release でも変更する場合があります。Programmatic integration は Configuration、CLI、公式 Python API、Archive semantics など明示された公開契約に依存させてください。

内部 module、repository-local development tools、文書生成 workspace はこの互換性方針の対象外です。

## Beta 期間の目的

Beta 期間では、特に次の点を確認します。

- 実際の project tree と共有用 Archive 作成で、現在の Configuration model が継続利用できること。
- CLI と公式 Python API が同じ invocation semantics を安定して提供できること。
- Scope、Selection、Base、Namespace、Output、Archive planning の主要契約に根本的な再設計が不要であること。
- 機能追加を既存の意味境界を崩さず additive に行えること。
- 文書、診断、platform compatibility など利用体験上の改善を継続できること。

## 1.0 への移行

十分な期間の実運用を経て、重大な設計上の問題や破壊的な再設計の必要がないと判断できた時点で、現在の設計を基礎として `1.0.0` へ移行します。

1.0 への移行条件は機能を際限なく追加することではありません。現在の公開 interface と filesystem / Archive model が、継続利用できる安定した契約として確認できることを重視します。

## 文書生成基盤

公開文書の canonical source / canonical document pipeline には `shikumi-devdoc>=0.3.0` を使用します。これは repository development 用 dependency であり、dirpluck の runtime dependency ではありません。

この source repository を Web 公開する時点では、必要な Shikumi 0.2.0 と shikumi-devdoc 0.3.0 が先に公開済みであることを前提とします。文書生成対象、出力先、project context など dirpluck 固有の orchestration は `tools/render_canonical_docs.py` に保持し、shikumi-devdoc の汎用 API へ project 固有情報を押し込みません。

## 配布上の留意点

現時点で dirpluck は **PyPI のみで公開**し、ソースリポジトリを閲覧できる公開 Web page はまだ設けない方針です。

このため、README やその他の公開文書に含まれる repository-relative な参照 link の一部は、PyPI 上では解決できません。これは現在の配布形態に起因する既知の制約です。

GitHub などでソースリポジトリを Web 公開した時点で、公開 repository の URL を基準に文書 link を見直し、公開環境から参照できる形へ修正します。

現時点では公開 repository がないため hosted CI も設けません。公開前の test、文書再生成 check、distribution 検証、PyPI への upload は local で行います。GitHub へ repository を公開した時点で、その公開環境に合わせて CI と release workflow を新たに構成します。
