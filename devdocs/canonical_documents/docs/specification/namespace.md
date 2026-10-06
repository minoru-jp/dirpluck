<!--
この文書は自動生成された翻訳元の canonical document です。
正本は `devdocs/canonical_sources/specification/namespace.py` です。
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

# Namespace

## SPEC_061

ネームスペースは `[namespace.<name>]` という名前付き table で定義する。現行 schema では table 本体は空でなければならず、属性を受理しない。親 `[namespace]` だけを空で定義することは Namespace definition にならないため error とする。

level: MUST

## SPEC_062

Namespace name は TOML key として解釈された後、1個の Archive directory component として検証する。空名、`.`、`..`、path separator の `/` と `\`、ASCII control character U+0000..U+001F と U+007F を拒否する。これらは host OS の filename rule ではなく、Archive entry name を安全な1 componentとして保持するための構造上の制約である。dirpluck は host OS ごとの予約名、末尾 dot、その他の filesystem 固有 naming rule を独自に判定しない。Namespace は filesystem path ではなく、source の logical Archive identity を補助する名前付き Configuration concept である。

level: MUST

## SPEC_063

Scope の `namespace` field は effective Namespace name を参照し、Layout を使用しない Target の final archive root に `NAMESPACE/` prefix を追加する。Scope root、Target discovery、Target entry name は変更しない。Unknown Namespace reference は Configuration error とする。同じ Scope に個別または `[about].targets_layout` 由来の effective Layout が存在する場合は Namespace と Layout を合成せず Configuration error とする。0.x compatibility として Always `namespace` を使用する source でも、個別または `[about].always_layout` 由来の effective Layout が同時に存在する場合は Namespace と Layout を合成せず Configuration error とする。Namespace だけを使用する Always の compatibility semantics は Compatibility specification に従う。

level: MUST

## SPEC_168

複数 Scope が同じ Namespace definition を参照すること自体は有効である。Namespace definition name は大文字小文字を区別しない比較で一意とする。Scope Namespace 適用後の final archive root は通常の Archive identity / collision rule に従う。実際に Archive へ書き込む spelling は Configuration / Target name の表記を保持する。

level: MAY

## SPEC_169

dirpluck は Archive directory identity について host OS / filesystem 固有の予約名、末尾 dot、Unicode normalization などを再現して cross-platform extraction compatibility を保証しない。別の OS / filesystem へ Archive を移動して展開する場合、その環境で有効かつ意図どおり区別される名前を選ぶ責任は Configuration author にある。大文字小文字を区別しない一意性検証は dirpluck 自身の Archive identity rule として適用する。

level: MUST
