# dirpluck Glossary

This glossary defines concepts used consistently across the `dirpluck` documentation and implementation. It defines only what the terms mean, not specification details such as cardinality constraints, resolution order, path bases, CLI grammar, validation, or error conditions.

## dirpluck

A tool that selects files from sources according to a declared extraction intent and produces a ZIP Archive. It exposes a CLI and a small Python API as entry points.

## Configuration file

A document identified by the `.dirpluck` filename extension whose TOML syntax describes a `dirpluck` extraction intent and the sources, selections, Output, and other definitions needed for that intent.

## Target

A source directory selected from a Scope at runtime and to which the Pluck selection is applied.

## Case

A named selection representing an extraction variation for the same source, distinct from its base selection.

## Always source

A source definition that fixes a source directory in the Configuration and participates in the same extraction intent on every run.

## Source

A filesystem directory that is subject to file selection in one run. Targets and Always sources differ in how the source participates in the run.

## Selection

The act of deciding which files from a source belong in the Archive according to declared patterns and policy, or the definition used to make that decision.

## Archive

The ZIP artifact produced by `dirpluck` from selection results.

## Output definition

A Configuration definition that declares where the generated Archive is written and how it is named.

## Archive README

An index document generated at the root of an Archive that describes the included sources and contents.

## pluck

The selection definition that describes what to extract from Targets selected for the current run.

## Shared pattern

A named reusable pattern set referenced by multiple selections.

## Base Configuration

A Configuration file referenced by another Configuration as its base, whose definitions are inherited and composed.

## Root Configuration

The outermost Configuration file selected by the CLI for one `dirpluck` run.

## Effective Configuration

The Configuration used for one run after resolving the Root Configuration and its base chain into the composed form.

## Scope

A range in the filesystem where Targets are searched for at runtime.

## Write boundary

A boundary that can be determined statically from the Configuration as the range in the filesystem within which one Output definition may write an Archive.

## Namespace

An Archive-only namespace added outside a source root to distinguish where sources are placed within an Archive.

## Invocation Template

A `.dirpluck-inv` document that stores execution inputs such as a Configuration, CLI Target references, and a Case as reusable invocations.
