"""Raw value occurrences preserve literal content and explicit source nulls."""

from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, XSD


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
EX = Namespace("https://example.test/")


class RawValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True, all_shapes=False, **options):
        # Isolate content rules here; the example and location suite validate
        # the complete schema, including required rows, columns, and views.
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
            use_shapes=None if all_shapes else [RAW.ValueContentShape], **options,
        )
        self.assertEqual(conforms, expected, report)

    def test_value_requires_literal_content_or_an_explicit_source_null(self):
        data = Graph()
        data.add((EX.value, RDF.type, RAW.Value))
        self.assert_valid(data, False)
        data.add((EX.value, RAW.literalValue, Literal("captured text")))
        self.assert_valid(data)

    def test_literals_keep_their_datatypes_and_language(self):
        literals = (
            Literal("00123"),
            Literal(0),
            Literal(False),
            Literal("12.50", datatype=XSD.decimal),
            Literal("2026-10-26", datatype=XSD.date),
            Literal("2026-10-26T12:30:00Z", datatype=XSD.dateTime),
            Literal("bonjour", lang="fr"),
        )
        for value in literals:
            with self.subTest(value=value):
                data = Graph()
                data.add((EX.value, RAW.literalValue, value))
                self.assert_valid(data, inplace=True)
                self.assertEqual(set(data.objects(EX.value, RAW.literalValue)), {value})
                self.assertIn((EX.value, RDF.type, RAW.Value), data)

    def test_empty_and_whitespace_strings_are_content(self):
        for text in ("", " ", "  padded\ttext\n", "NULL", "null"):
            with self.subTest(text=text):
                data = Graph()
                data.add((EX.value, RAW.literalValue, Literal(text)))
                self.assert_valid(data, inplace=True)
                self.assertEqual(set(data.objects(EX.value, RAW.literalValue)), {Literal(text)})
                self.assertNotIn((EX.value, RDF.type, RAW.NullValue), data)

    def test_explicit_source_null_has_no_literal_content(self):
        for node in (EX.value, BNode()):
            with self.subTest(node=node):
                data = Graph()
                data.add((node, RDF.type, RAW.NullValue))
                self.assert_valid(data, inplace=True)
                self.assertIn((node, RDF.type, RAW.Value), data)
                self.assertEqual(list(data.objects(node, RAW.literalValue)), [])
                data.add((node, RAW.literalValue, Literal("")))
                self.assert_valid(data, False)

    def test_literal_content_is_one_literal_not_an_iri_or_blank_node(self):
        for value in (EX.resource, BNode()):
            with self.subTest(value=value):
                data = Graph()
                data.add((EX.value, RAW.literalValue, value))
                self.assert_valid(data, False)
        data = Graph()
        data.add((EX.value, RAW.literalValue, Literal("first")))
        data.add((EX.value, RAW.literalValue, Literal("second")))
        self.assert_valid(data, False)

    def test_source_text_preserves_lexical_details_without_becoming_content(self):
        data = Graph()
        data.add((EX.value, RAW.literalValue, Literal(7)))
        data.add((EX.value, RAW.sourceText, Literal("0007")))
        self.assert_valid(data, inplace=True)
        self.assertEqual(set(data.objects(EX.value, RAW.literalValue)), {Literal(7)})
        self.assertEqual(set(data.objects(EX.value, RAW.sourceText)), {Literal("0007")})
        data.remove((EX.value, RAW.literalValue, None))
        self.assert_valid(data, False)

    def test_source_text_is_at_most_one_string_and_can_record_a_null_marker(self):
        data = Graph()
        data.add((EX.value, RDF.type, RAW.NullValue))
        data.add((EX.value, RAW.sourceText, Literal("\\N")))
        self.assert_valid(data)
        for value in (EX.text, Literal(7), Literal("texte", lang="fr")):
            with self.subTest(value=value):
                invalid = Graph()
                invalid.add((EX.value, RAW.literalValue, Literal("value")))
                invalid.add((EX.value, RAW.sourceText, value))
                self.assert_valid(invalid, False)
        data.add((EX.value, RAW.sourceText, Literal("another marker")))
        self.assert_valid(data, False)

    def test_untyped_and_subclassed_occurrences_cannot_bypass_content_checks(self):
        for predicate in (RAW.valueOf, RAW.forPredicate):
            with self.subTest(predicate=predicate):
                data = Graph()
                data.add((EX.value, predicate, EX.resource))
                self.assert_valid(data, False)
        for parent in (RAW.Value, RAW.NullValue):
            with self.subTest(parent=parent):
                data = Graph()
                data.add((EX.specialValue, RDFS.subClassOf, parent))
                data.add((EX.value, RDF.type, EX.specialValue))
                self.assert_valid(data, parent == RAW.NullValue)
                data.add((EX.value, RAW.literalValue, Literal("value")))
                self.assert_valid(data, parent == RAW.Value)

    def test_value_occurrence_must_be_a_resource(self):
        data = Graph()
        data.add((Literal("not an occurrence"), RAW.literalValue, Literal("content")))
        self.assert_valid(data, False)

    def test_owl_infers_value_types_without_inventing_content_or_nulls(self):
        data = Graph()
        data.add((EX.literal, RAW.literalValue, Literal(7)))
        data.add((EX.null, RDF.type, RAW.NullValue))
        data.add((EX.unknown, RDF.type, RAW.Value))
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertIn((EX.literal, RDF.type, RAW.Value), graph)
        self.assertIn((EX.null, RDF.type, RAW.Value), graph)
        self.assertNotIn((EX.unknown, RDF.type, RAW.NullValue), graph)
        self.assertEqual(list(graph.objects(EX.unknown, RAW.literalValue)), [])

    def test_content_shapes_pass_standard_shacl_meta_validation(self):
        data = Graph()
        data.add((EX.value, RAW.literalValue, Literal("content")))
        self.assert_valid(data, meta_shacl=True)

    def test_documented_value_examples_validate(self):
        text = (ROOT / "docs/raw-data.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data, all_shapes=True)
        self.assertEqual(set(data.objects(EX.paddedNumber, RAW.sourceText)), {Literal("0007")})
        self.assertEqual(set(data.objects(EX.empty, RAW.literalValue)), {Literal("")})
        self.assertIn((EX.null, RDF.type, RAW.NullValue), data)


if __name__ == "__main__":
    unittest.main()
