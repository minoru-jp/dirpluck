from shikumi_devdoc.norms.document import canonical, title, vocabulary, vocabulary_refs

from canonical_documents import terms


@canonical
@vocabulary(terms)
@title("{{TERM_1}}")
class TITLE_1:
    r'''{{TERM_1}} は、「どの file を一緒に扱うか」という判断を TOML に残し、その宣言から ZIP Archive を組み立てる tool です。CLI を主な入口とし、同じ invocation model を最小の Python API からも利用できます。

Backup のように周辺をすべて複製するのではなく、review、引き渡し、調査、定例作業、LLM と扱う作業 context など、ある目的に必要な file だけを繰り返し集めることを目的としています。'''
    vocabulary_refs @= (terms.TERM_1,)

    @title("何に使うか")
    class TITLE_2:
        r''''''

        @title("必要な資料をひとつにまとめる")
        class TITLE_3:
            r'''複数の directory に分かれた資料でも、同じ目的で使うものならひとつの Archive にまとめられます。

たとえば review 用に、

- 対象 project の source
- review guideline
- reference material

を一緒に集める、といった用途です。

固定資料だけを集めることも、実行時に選んだ {{TERM_3}} へ固定資料を添えることもできます。'''
            vocabulary_refs @= (terms.TERM_3,)

        @title("同じ抽出方法を、別の Target に使う")
        class TITLE_4:
            r'''「README と `src/` と `tests/` を集める」「秘密情報や生成物は除外する」といった判断を {{TERM_2}} に残しておけば、対象となる project を変えながら同じルールを使えます。

{{TERM_3}} をどこから選ぶかは {{TERM_16}} として分けられるため、Configuration の置き場所と実際の project tree を同じ場所に揃える必要はありません。'''
            vocabulary_refs @= (terms.TERM_2, terms.TERM_3, terms.TERM_16)

    @title("なぜ宣言として残すのか")
    class TITLE_5:
        r'''一度だけなら、手作業で ZIP を作る方が簡単です。

{{TERM_1}} が役立つのは、同じ種類の判断を後でもう一度行うときです。

Configuration に残しておけば、

- 何を必ず含めるか
- 何を存在するときだけ含めるか
- 何を除外するか
- どの固定資料を一緒に集めるか

を、shell history、会話履歴、人間の記憶へ依存せず確認できます。

`--preview` を使えば、Archive を書き込む前に、現在の filesystem に対して何が選ばれるかを確認できます。

Configuration を複数の用途で共有したい場合は、別の Configuration を基礎として再利用することもできます。Configuration の構成方法については `docs/CONFIGURATION.md`、厳密な合成・解決規則については `docs/SPECIFICATION.md` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("外へ渡す前に")
    class TITLE_6:
        r'''{{TERM_1}} は、どの file が機密情報かを推論しません。

外部へ渡す Archive を作る場合は、`--preview` で内容を確認し、含めるべきでないものを Configuration で明示的に除外してください。

たとえば `.env`、秘密鍵、credential、project 固有の機密 file などは、名前や配置が project ごとに異なります。

Configuration と filesystem 操作の trust boundary、absolute path、overwrite、外部へ渡す Archive を扱う際の考え方は `docs/TRUST.md` にまとめています。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("小さな例")
    class TITLE_7:
        r'''`--config` を指定しない場合、{{TERM_1}} はカレントディレクトリの `default.dirpluck` を使用します。まずはこの既定の Configuration を使うのが、もっとも簡単な始め方です。

次の内容を `default.dirpluck` として保存します。

```toml
[about]
description = "Review package for the example project."

[pluck]
description = "Project files selected for review."
must = ["README.md", "src", "tests"]
ignore = [".git/", "__pycache__/", "*.pyc"]

[always.guidelines]
path = "review-guidelines"
description = "Review guidelines shared across projects."
must = ["*.md"]

[output]
path = "review.zip"
```

たとえば同じ directory に、次のような file があるとします。

```text
.
├── default.dirpluck
├── example/
│   ├── README.md
│   ├── src/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
└── review-guidelines/
    └── review.md
```

まず `--preview` で、Archive に何が入るかを確認できます。

```console
{{TERM_1}} example --preview
```

この例では、次のように表示されます。

```text
├── README.md
├── example/
│   ├── README.md
│   ├── src/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
└── review-guidelines/
    └── review.md
```

先頭の `README.md` は、{{TERM_1}} が Archive の内容を説明するために生成する file です。

問題がなければ、同じ Target で Archive を作成します。

```console
{{TERM_1}} example
```

`[output]` に従って `review.zip` が作成されます。その中には preview で確認した file と、生成された `README.md` が入ります。

この例で生成される `README.md` は次の内容です。

```markdown
# Archive contents

Review package for the example project.

## `example/`

Files: 3

Project files selected for review.

## `review-guidelines/`

Files: 1

Review guidelines shared across projects.
```

Configuration に書いた `description` は、この Archive README の説明として使われます。

- `[about].description` は Archive 全体の説明になります。
- `[pluck].description` は Target から集めた source の説明になります。
- `[always.guidelines].description` は固定して集めた `review-guidelines/` の説明になります。

これらの `description` は任意です。説明が不要なら省略でき、source の `description` を省略しても抽出意味論は変わりません。

このように、Configuration には「何を集めるか」だけでなく、「その Archive が何のためのものか」という人間向けの context も必要に応じて残せます。

この例では既定の {{TERM_16}} から Target を選び、そのまま Archive の root へ配置しています。より大きな構成では、{{TERM_16}} を追加して Target を選ぶ filesystem 上の範囲を分けたり、{{TERM_18}} で source を Archive 内の明示的な path の下へ整理したりできます。

同じ Configuration、Target、Case の組み合わせを繰り返し使う場合は、{{TERM_19}} に呼び出し方を保存できます。ひとつの Invocation Template に複数の named Invocation を持たせることもできるため、review、docs、release といった用途ごとの呼び出しを同じ file にまとめられます。

Configuration の各 field、Scope、Case、Always、Output、Namespace などの詳しい書き方は `docs/CONFIGURATION.md` を参照してください。CLI option、Configuration の選択、Invocation Template の使い方は `docs/CLI.md` にまとめています。'''
        vocabulary_refs @= (terms.TERM_1, terms.TERM_16, terms.TERM_18, terms.TERM_19)

    @title("インストール")
    class TITLE_8:
        r'''現在の version は **{{version}}** です。

Python 3.11 以降を使用します。

```console
pip install {{TERM_1}}
{{TERM_1}} --version
```

{{TERM_1}} には runtime third-party dependency はありません。'''
        vocabulary_refs @= (terms.TERM_1,)

    @title("文書")
    class TITLE_9:
        r'''文書は目的ごとに分けています。

- `GLOSSARY.md`: 文書全体で使う概念の意味。
- `docs/CONFIGURATION.md`: `.dirpluck` Configuration を書くための guide。
- `docs/CLI.md`: CLI の使い方と `.dirpluck-inv` Invocation Template の guide。
- `docs/PYTHON_API.md`: CLI と同じ実行 model を Python から使う最小の公式 API。
- `docs/SPECIFICATION.md`: Configuration composition、resolution、matching、filesystem traversal、Archive、Output、validation の厳密な規則。
- `docs/TRUST.md`: Configuration と filesystem 操作の trust boundary、および利用者が確認すべき範囲。
- `CHANGELOG.md`: release history。'''

    @title("ライセンス")
    class TITLE_10:
        r'''{{TERM_1}} は MIT License のもとで公開されています。

詳細は `LICENSE` を参照してください。'''
        vocabulary_refs @= (terms.TERM_1,)
