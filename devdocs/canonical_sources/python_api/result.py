from devdocs.canonical_sources.vocabulary.canonical import TERMS
from shikumi_devdoc.fields.api_reference import OPERATION, TYPE, VALUE, input, kind, name, output
from shikumi_devdoc.fields.lifecycle import introduced
from shikumi_devdoc.norms.common import canonical_source, merge, summary
from shikumi_devdoc.norms.document import test_target_field, title


preview_example = test_target_field("preview example")
result_fields = test_target_field("RunResult public fields")


@summary('preview/build の結果として返す `RunResult` とその公開 field。')


@canonical_source('RunResult', filename='result.md', order=20, placeholders=False, heading="title")
class API_REFERENCE_PART:
    r"""
    `preview=True` は Archive file を書き込まず、CLI `--preview` と同じ planning semantics を実行します。Output を解決・書き込みしないため、`output`、`force=True`、`sequence` とは組み合わせません。

    ```python
    {{preview_example}}
    ```

    `RunResult` は次の public field を持ちます。

    ```text
    {{result_fields}}
    ```

    通常 build でも `preview_text` と `archive_readme` は実際に使用した plan から返します。そのため、呼び出し側は CLI output を parse せず、生成結果と plan の主要な public information を取得できます。
    """

    preview_example @= """
    result = dirpluck.run("example", preview=True)
    print(result.preview_text)
    """
    result_fields @= """
    output_path         build で生成した ZIP path。preview では None
    preview_text        CLI --preview と同じ tree representation
    archive_entries     実際に Archive へ入る final entry path の tuple
    archive_readme      root README.md として生成する Markdown
    skipped_link_count  automatic traversal で除外した link-like entry 数
    invocation_empty    選択した Invocation が config / targets / case / archive_mtime を持たなかったか
    """

    name @= "RunResult"
    kind @= TYPE
    introduced @= "0.9.0"
    output @= "output_path"
    output @= "preview_text"
    output @= "archive_entries"
    output @= "archive_readme"
    output @= "skipped_link_count"
    output @= "invocation_empty"
