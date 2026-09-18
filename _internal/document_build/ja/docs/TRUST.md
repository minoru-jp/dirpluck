<!-- shikumi-devdoc:translation-metadata
{
  "version": 1,
  "publication": "omit-this-comment",
  "preserve_spelling": [
    {
      "source": "dirpluck_docs.vocabulary.canonical",
      "identifier": "TERM_1",
      "text": "dirpluck"
    }
  ]
}
-->

<!--
この文書は自動生成された翻訳元の中間文書です。
正本は `dirpluck_docs/trust/canonical.py` です。
直接編集しないでください。

公開文書作成方針

- `_internal/document_build/ja/` にある日本語中間文書はリポジトリへ commit し、正本からの実現結果をレビュー可能にする。
- 公開文書はこの中間文書を翻訳元とする。
- 翻訳では意味、構造、情報量を維持し、内容を勝手に追加・削除・要約しない。
- `preserve_spelling @= True` が指定された用語は表記を変更しない。
- コード、Python 識別子、コマンド、ファイルパス、URL は、翻訳上の必要がない限り変更しない。
- このコメントブロックと翻訳メタデータは公開文書には含めない。
- 内容の変更は公開文書や中間文書を直接編集するのではなく、正本へ戻って行う。
-->

# dirpluck Trust Model

この文書は、dirpluck の Configuration と filesystem 操作をどの信頼境界で扱うかを説明します。正確な path resolution、selection、output semantics は `SPECIFICATION.md` を参照してください。

## Configuration は実行指示です

設定ファイルは、どの filesystem location から何を選び、どこへ Archive を書くかを宣言します。dirpluck は、その宣言が利用者の意図に対して適切か、参照先が機密か、description が実態と一致するかを推論しません。

Configuration を第三者から受け取った場合や、内容を自分で確認していない場合は、実行前に source、selection、output を確認してください。Configuration は sandbox policy や capability manifest ではなく、dirpluck に渡す実行指示として扱います。

## Filesystem permission が実際の権限境界です

dirpluck は OS の permission を越えて file を読む、または書く機能を持ちません。一方で、実行 user がアクセスでき、Configuration の path 規則で参照できる場所は source や output として指定できます。Relative `..` や absolute path も、そのための明示的な filesystem location です。

Source boundary、symbolic-link escape、archive path collision、Configuration schema などの structural validation は行いますが、それらは declared filesystem operation の目的や安全性を判定する guard ではありません。

## Selection の内容は利用者が決めます

Directory を include すると、その配下は exclude と symbolic-link rules に従って収集候補になります。Hidden file、repository metadata、environment file、key material などを filename や内容から推論して自動除外することはありません。

外部へ渡す Archive を作る場合は、Configuration の include / exclude と生成内容を、その用途に応じて確認してください。`--dry-run` は archive-relative な contents plan を確認するために利用できます。

## Output は宣言された policy に従います

Output filename の extension は ZIP format の判定には使いません。Configuration が指定した output location と `if_exists` policy に従って ZIP Archive を生成します。`if_exists = "overwrite"` を指定した場合は、その output path に存在する file を置き換える意図を明示したものとして扱います。

Output path と既存 file の扱いは、実行前に Configuration で確認してください。

## Archive を外部へ渡すとき

生成されるアーカイブREADMEは、既定では source filesystem path を記録しません。`--paths` を指定した場合だけ、索引に解決済み source directory を含めます。Absolute path などローカル環境の情報を含み得るため、外部へ渡す Archive で `--paths` を使う場合は内容を確認してください。

Archive 自体に含まれる file の選択は Configuration に従います。README から source path を隠すことは、Archive contents を検査または sanitize する機能ではありません。

## LLM-assisted work での位置付け

LLM-assisted work では、dirpluck はローカル filesystem 上の必要な材料を focused Archive として用意するために使えます。非ローカルの対話型 LLM へ upload したり、ローカル agent 型の LLM が使う workspace へ配置したりする受け渡し物を作る用途です。

dirpluck 自体が LLM にローカル filesystem access を与える仕組みではなく、LLM が dirpluck を直接操作することも前提にしません。誰が Configuration を作成した場合でも、実行時の trust boundary は同じです。
