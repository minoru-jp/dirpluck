import unittest

from dirpluck._target_models import (
    ParsedTargetReference,
    TargetEntryExpr,
    TargetItem,
    TargetListExpr,
    TargetRegexExpr,
    TargetScopeExpr,
)
from dirpluck._target_syntax import parse_target_reference
from dirpluck.errors import SelectionError


class TargetSyntaxTests(unittest.TestCase):
    def parse(self, reference: str, *scope_names: str | None) -> ParsedTargetReference:
        return parse_target_reference(
            reference,
            scope_names=scope_names,
            label="target reference",
        )

    def test_unnamed_scope_file_and_directory_forms_are_typed(self):
        self.assertEqual(
            self.parse("artifact.zip", None),
            ParsedTargetReference(
                None,
                TargetEntryExpr(TargetItem("artifact.zip", "file")),
            ),
        )
        self.assertEqual(
            self.parse("./project/", None),
            ParsedTargetReference(
                None,
                TargetEntryExpr(TargetItem("project", "directory")),
            ),
        )

    def test_scope_expansion_and_named_entries_are_distinct_expressions(self):
        self.assertEqual(
            self.parse("/", None),
            ParsedTargetReference(None, TargetScopeExpr()),
        )
        self.assertEqual(
            self.parse("work/", None, "work"),
            ParsedTargetReference("work", TargetScopeExpr()),
        )
        self.assertEqual(
            self.parse("work/project/", None, "work"),
            ParsedTargetReference(
                "work",
                TargetEntryExpr(TargetItem("project", "directory")),
            ),
        )

    def test_list_selector_consumes_file_directory_markers(self):
        self.assertEqual(
            self.parse("work:[a.zip/b//c.txt]", None, "work"),
            ParsedTargetReference(
                "work",
                TargetListExpr(
                    (
                        TargetItem("a.zip", "file"),
                        TargetItem("b", "directory"),
                        TargetItem("c.txt", "file"),
                    )
                ),
            ),
        )

    def test_regex_selector_is_validated_and_compiled_during_parsing(self):
        parsed = self.parse("work:<.*\\.zip>", None, "work")
        self.assertEqual(parsed.scope, "work")
        expression = parsed.expression
        self.assertIsInstance(expression, TargetRegexExpr)
        assert isinstance(expression, TargetRegexExpr)
        self.assertEqual(expression.pattern_text, ".*\\.zip")
        self.assertIsNotNone(expression.pattern.fullmatch("artifact.zip"))

    def test_longest_configured_scope_name_wins_for_colon_selectors(self):
        self.assertEqual(
            self.parse("foo:bar:[a.zip]", None, "foo", "foo:bar"),
            ParsedTargetReference(
                "foo:bar",
                TargetListExpr((TargetItem("a.zip", "file"),)),
            ),
        )

    def test_unknown_named_selector_remains_a_selector_expression(self):
        parsed = self.parse("missing:[a.zip]", None, "known")
        self.assertEqual(parsed.scope, "missing")
        self.assertIsInstance(parsed.expression, TargetListExpr)

    def test_literal_colon_remains_available_in_ordinary_target_names(self):
        self.assertEqual(
            self.parse("foo:bar", None, "foo"),
            ParsedTargetReference(
                None,
                TargetEntryExpr(TargetItem("foo:bar", "file")),
            ),
        )

    def test_invalid_list_and_regex_syntax_is_rejected_before_resolution(self):
        invalid = (
            ":[a///b]",
            ":[a//]",
            ":[/a]",
            ":[a",
            ":<([>",
            ":<abc",
        )
        for reference in invalid:
            with self.subTest(reference=reference), self.assertRaises(SelectionError):
                self.parse(reference, None)


if __name__ == "__main__":
    unittest.main()
