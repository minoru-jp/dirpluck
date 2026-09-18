# dirpluck Trust Model

This document explains the trust boundary for `dirpluck` Configurations and filesystem operations. For exact path resolution, selection, and output semantics, see [SPECIFICATION.md](SPECIFICATION.md).

## A Configuration is an execution instruction

A Configuration declares what to select from which filesystem locations and where to write the Archive. `dirpluck` does not infer whether that declaration is appropriate for the user's intent, whether a referenced location is sensitive, or whether a `description` accurately represents its contents.

If a Configuration comes from a third party or has not been reviewed, inspect its sources, selections, and output before running it. Treat a Configuration as an execution instruction given to `dirpluck`, not as a sandbox policy or capability manifest.

## Filesystem permissions are the actual authority boundary

`dirpluck` cannot read or write beyond the permissions of the user running it. Conversely, locations that the user can access and that the Configuration path rules can reference may be used as sources or output locations. Relative `..` paths and absolute paths are explicit ways to name such filesystem locations.

`dirpluck` still performs structural validation such as source-boundary enforcement, symbolic-link escape checks, archive-path collision checks, and Configuration-schema validation. Those checks are not a guard that decides whether a declared filesystem operation is appropriate or safe for a particular purpose.

## The user decides what belongs in a selection

Including a directory makes files below it candidates for collection, subject to exclude and symbolic-link rules. `dirpluck` does not infer from filenames or contents that hidden files, repository metadata, environment files, key material, or similar files should be excluded automatically.

When creating an Archive that will be shared outside the local environment, review the Configuration's include and exclude rules and the resulting contents for that purpose. `--dry-run` can be used to inspect the archive-relative contents plan.

## Output follows the declared policy

The output filename extension is not used to determine the ZIP format. `dirpluck` writes a ZIP Archive according to the configured output location and `if_exists` policy. Setting `if_exists = "overwrite"` explicitly declares that an existing file at the output path may be replaced.

Review the output path and existing-file policy in the Configuration before running it when those locations matter.

## When an Archive leaves the local environment

The generated Archive README omits source filesystem paths by default. Only `--paths` adds each resolved source directory to the index. Because those values may expose local information such as absolute paths, review the Archive when using `--paths` for material that will be shared externally.

The files included in the Archive are still selected according to the Configuration. Hiding source paths from the README is not inspection or sanitization of the Archive contents.

## Position in LLM-assisted work

For LLM-assisted work, `dirpluck` can prepare the required local material as a focused Archive. That Archive can be uploaded to a non-local conversational LLM or placed into a workspace used by a local agent.

`dirpluck` does not itself grant an LLM access to the local filesystem, and it does not assume that an LLM operates `dirpluck` directly. The same trust boundary applies regardless of who authored the Configuration.
