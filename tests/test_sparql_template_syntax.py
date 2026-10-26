"""Native dollar-prefixed SPARQL variables differ from template substitution."""

import unittest

from pyparsing import ParseException
from rdflib import Graph, Literal, Namespace
from rdflib.plugins.sparql.parser import parseQuery


EX = Namespace("https://example.test/")
QUERY = "SELECT ?customer WHERE { ?customer <https://example.test/identifier> $m }"


class SparqlTemplateSyntaxTests(unittest.TestCase):
    def fixture(self):
        graph = Graph()
        graph.add((EX.alice, EX.identifier, Literal("A123")))
        graph.add((EX.bob, EX.identifier, Literal("B456")))
        return graph

    def test_dollar_and_question_mark_sigils_identify_the_same_query_variable(self):
        graph = self.fixture()
        for query in (
            'SELECT $m WHERE { $m <https://example.test/identifier> "A123" }',
            'SELECT ?m WHERE { ?m <https://example.test/identifier> "A123" }',
            'SELECT ?m WHERE { $m <https://example.test/identifier> "A123" }',
        ):
            with self.subTest(query=query):
                self.assertEqual(list(graph.query(query)), [(EX.alice,)])

    def test_a_dollar_variable_is_unbound_unless_a_value_is_supplied(self):
        graph = self.fixture()
        self.assertEqual(set(graph.query(QUERY)), {(EX.alice,), (EX.bob,)})
        self.assertEqual(list(graph.query(QUERY, initBindings={"m": Literal("A123")})),
                         [(EX.alice,)])

    def test_a_braced_template_placeholder_is_not_native_sparql_syntax(self):
        with self.assertRaises(ParseException):
            parseQuery(QUERY.replace("$m", "${m}"))


if __name__ == "__main__":
    unittest.main()
