# RunResult

`preview=True` performs the same planning semantics as CLI `--preview` without writing an Archive file. Because it does not resolve or write an Output, it cannot be combined with `output`, `force=True`, or `sequence`.

```python
result = dirpluck.run("example", preview=True)
print(result.preview_text)
```

`RunResult` exposes these public fields:

```text
output_path         ZIP path created by a build; None for preview
preview_text        the same tree representation used by CLI --preview
archive_entries     tuple of final entry paths that belong in the Archive
archive_readme      Markdown generated as the root README.md
skipped_link_count  number of link-like entries excluded during automatic traversal
invocation_empty    whether the selected Invocation had no config / targets / case / archive_mtime
warnings            tuple of non-fatal planning diagnostics
```

A normal build also returns `preview_text` and `archive_readme` from the exact plan used for the build. When planning produces a non-fatal diagnostic, `warnings` contains the human-readable messages that the CLI prints to stderr. Configuration-syntax deprecations are not planning diagnostics, so they are not included in `RunResult.warnings`; the Python API reports them through the standard warnings framework as the public `ConfigurationDeprecationWarning` (`FutureWarning` subclass). Callers therefore do not need to parse CLI output to inspect the main public information about the planned or generated Archive, while Configuration migration can be managed independently with Python warning filters.
