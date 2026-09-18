from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from dirpluck_docs.vocabulary import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}}")
class TITLE_1:
    r'''{{TERM_1}} は、繰り返し現れる「どのファイルを一緒に扱うか」という判断を TOML に残し、同じ意図から ZIP アーカイブを組み立てる CLI ツールです。

バックアップのように周辺をすべて複製するのではなく、レビュー、引き渡し、調査、定例作業、LLM と扱う作業コンテキストなど、明示した目的に必要な範囲だけをまとめることを目的とします。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("何に使うか")
    class TITLE_2:
        r''''''

        @title("固定された複数の資料をひとつにまとめる")
        class TITLE_3:
            r'''必要な資料が別々のディレクトリに置かれていても、それらが同じ目的に属するなら、{{TERM_5}}として{{TERM_2}}へ固定できます。Companion の source directory は Configuration の近くに置く必要はなく、filesystem 上の別の場所を直接参照できます。

たとえば提案資料、調査結果、法務資料をひとつのレビュー用パッケージにしたり、週次作業で毎回同じ種類の資料を集めたりできます。実行時に変わる対象がない用途では、Companion だけでもアーカイブを作れます。'''
            vocabulary_refs @= (terms.TERM_2, terms.TERM_5)

        @title("実行ごとに変わる対象へ固定資料を付ける")
        class TITLE_4:
            r'''異なるプロジェクト、提出物、案件などへ毎回同じ選択規則を適用したい場合は、{{TERM_3}}を使います。Target の選択規則は Configuration に残し、実際の{{TERM_6}}は実行時に与えます。

固定ガイドライン、テンプレート、参照資料などは Companion として同じアーカイブへ加えられます。これにより、対象だけを変えながら同じ抽出意図を繰り返せます。'''
            vocabulary_refs @= (terms.TERM_3, terms.TERM_6)

        @title("別の Configuration が表す抽出意図を再利用する")
        class TITLE_5:
            r'''関連するプロジェクトに既に{{TERM_2}}がある場合は、{{TERM_13}}でその定義を内側の layer として利用できます。親側で同じ情報をコピーする必要はありません。

Import の解決順序、shadowing、filesystem boundary などの厳密な規則は `docs/SPECIFICATION.md` にまとめています。Configuration を書くために必要な形だけを知りたい場合は `docs/CONFIGURATION.md` を参照してください。'''
            vocabulary_refs @= (terms.TERM_2, terms.TERM_13)

    @title("宣言として残す理由")
    class TITLE_6:
        r'''一度きりなら手作業で ZIP を作る方が簡単です。{{TERM_1}} が役立つのは、同じ種類の判断を後でもう一度行うときです。

Configuration に残しておけば、何を含めるか、何を任意扱いにするか、何を除外するか、どの固定資料を伴わせるかを、シェル履歴や会話履歴、人間の記憶へ依存せず確認できます。`--dry-run` を使えば、出力を書き込む前に現在の filesystem に対する解決結果を確認できます。

LLM と扱う作業でも、dirpluck の役割はローカル filesystem から必要な材料を選んで Archive を用意するところまでです。非ローカルの対話型 LLM にはその Archive をアップロードし、ローカル agent 型の LLM では workspace へ配置する受け渡し物として使えます。LLM が dirpluck を操作することを前提としません。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("Configuration と filesystem の信頼境界")
    class TITLE_7:
        r'''外部へ渡す Archive を作る場合は、作成前に selection を確認してください。{{TERM_1}} はどの file が機密かを推論しないため、含めるべきでないものは `exclude` で明示します。たとえば次のように書けます。

```toml
exclude = [".git/", ".env*", "*.pem", "*.key"]
```

これは一例であり、project 固有の機密情報は別の名前や場所に存在し得ます。Configuration をどのような入力として扱うか、absolute path、overwrite、外部へ渡す Archive の確認責任などは `docs/TRUST.md` にまとめています。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("小さな例")
    class TITLE_8:
        r'''次の Configuration は、実行時の Target と固定ガイドラインをひとつのアーカイブへまとめます。

```toml
[target]
description = "The project currently under review."
include_if_exists = ["README.md", "src", "tests"]
exclude = [".git/", "__pycache__/", "*.pyc"]
if_empty = "allow"

[companion.guidelines]
path = "review-guidelines"
description = "Guidelines used for every review."
include = ["*.md"]

[output]
path = "artifacts/review.zip"
if_exists = "overwrite"
```

```console
{{TERM_1}} projects/example --dry-run
{{TERM_1}} projects/example
```

TOML の各 field とより大きな例は `docs/CONFIGURATION.md`、CLI option と Configuration discovery は `docs/CLI.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("インストール")
    class TITLE_9:
        r'''Python 3.11 以降を使用します。現在のリリースは `{{version}}` です。

```console
pip install {{TERM_1}}
{{TERM_1}} --version
```

実行時のサードパーティ依存はありません。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("文書")
    class TITLE_10:
        r'''文書は読む目的で分けています。

- `GLOSSARY.md`: 文書全体で使う概念の意味。
- `docs/CONFIGURATION.md`: TOML Configuration を書くためのガイド。
- `docs/CLI.md`: CLI を実行するためのガイド。
- `docs/SPECIFICATION.md`: 解決、matching、filesystem、archive、output、validation の厳密な規則。
- `docs/TRUST.md`: Configuration と filesystem 操作の信頼境界、確認すべき責任範囲。
- `CHANGELOG.md`: リリース履歴。

wheel には、インストール後すぐ Configuration を書いて CLI を実行できるよう、簡潔な `dirpluck/docs/CONFIGURATION.md` と `dirpluck/docs/CLI.md` に加えて、同じ trust model を説明する `dirpluck/docs/TRUST.md` を同梱します。より詳しい説明が必要な場合は、sdist またはリポジトリに含まれる上記文書を参照してください。'''

    @title("公開インターフェース")
    class TITLE_11:
        r'''互換性を保証する公開面は `dirpluck` CLI と TOML Configuration 形式です。パッケージ内の Python モジュールは、明示的に公開 API とされない限り内部実装として扱います。'''
