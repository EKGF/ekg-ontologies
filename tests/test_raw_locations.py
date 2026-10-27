"""Captured values identify physical columns within their rows' views."""

from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
EX = Namespace("https://example.test/")


class RawLocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True, **options):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False, **options,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self, direction="forward"):
        data = Graph()
        data.add((EX.value, RAW.literalValue, Literal("captured")))
        data.add((EX.value, RAW.valueOf, EX.row))
        data.add((EX.value, RAW.forColumn, EX.column))
        data.add((EX.row, RAW.isRowInView, EX.view))
        if direction in ("forward", "both"):
            data.add((EX.view, RAW.hasColumn, EX.column))
        if direction in ("inverse", "both"):
            data.add((EX.column, RAW.isColumnInView, EX.view))
        return data

    def test_both_column_membership_directions_infer_types_and_inverse_links(self):
        for direction in ("forward", "inverse", "both"):
            with self.subTest(direction=direction):
                data = self.fixture(direction)
                self.assert_valid(data)
                graph = self.ontology + data
                DeductiveClosure(OWLRL_Semantics).expand(graph)
                for node, kind in ((EX.value, RAW.Value), (EX.row, RAW.Row),
                                   (EX.column, RAW.Column), (EX.view, RAW.View)):
                    self.assertIn((node, RDF.type, kind), graph)
                self.assertIn((EX.view, RAW.hasColumn, EX.column), graph)
                self.assertIn((EX.column, RAW.isColumnInView, EX.view), graph)

    def test_each_value_requires_one_row_and_one_column(self):
        for missing in (RAW.valueOf, RAW.forColumn):
            with self.subTest(missing=missing):
                data = self.fixture()
                data.remove((EX.value, missing, None))
                self.assert_valid(data, False)
        for predicate, extra in ((RAW.valueOf, EX.otherRow),
                                 (RAW.forColumn, EX.otherColumn)):
            with self.subTest(predicate=predicate):
                data = self.fixture()
                data.add((EX.value, predicate, extra))
                if predicate == RAW.valueOf:
                    data.add((extra, RAW.isRowInView, EX.view))
                else:
                    data.add((EX.view, RAW.hasColumn, extra))
                self.assert_valid(data, False)

    def test_column_requires_one_view_counting_both_directions(self):
        data = Graph()
        data.add((EX.column, RDF.type, RAW.Column))
        self.assert_valid(data, False)
        data.add((EX.view, RAW.hasColumn, EX.column))
        self.assert_valid(data)
        data.add((EX.column, RAW.isColumnInView, EX.view))
        self.assert_valid(data)
        for direction in ("forward", "inverse"):
            with self.subTest(direction=direction):
                invalid = data + Graph()
                if direction == "forward":
                    invalid.add((EX.otherView, RAW.hasColumn, EX.column))
                else:
                    invalid.add((EX.column, RAW.isColumnInView, EX.otherView))
                self.assert_valid(invalid, False)

    def test_row_requires_one_view(self):
        data = Graph()
        data.add((EX.row, RDF.type, RAW.Row))
        self.assert_valid(data, False)
        data.add((EX.row, RAW.isRowInView, EX.view))
        self.assert_valid(data)
        data.add((EX.row, RAW.isRowInView, EX.otherView))
        self.assert_valid(data, False)

    def test_row_and_column_must_belong_to_the_same_view(self):
        for direction in ("forward", "inverse", "both"):
            with self.subTest(direction=direction):
                data = self.fixture(direction)
                data.set((EX.row, RAW.isRowInView, EX.otherView))
                self.assert_valid(data, False)

    def test_missing_row_or_column_view_is_rejected(self):
        for relation in ("row", "column"):
            with self.subTest(relation=relation):
                data = self.fixture()
                if relation == "row":
                    data.remove((EX.row, RAW.isRowInView, None))
                else:
                    data.remove((EX.view, RAW.hasColumn, None))
                self.assert_valid(data, False)

    def test_link_endpoints_must_be_resources(self):
        for subject, predicate in ((EX.value, RAW.valueOf), (EX.value, RAW.forColumn),
                                   (EX.row, RAW.isRowInView),
                                   (EX.column, RAW.isColumnInView)):
            with self.subTest(predicate=predicate):
                data = self.fixture("inverse")
                data.set((subject, predicate, Literal("invalid endpoint")))
                self.assert_valid(data, False)
        data = self.fixture()
        data.set((EX.view, RAW.hasColumn, Literal("invalid column")))
        self.assert_valid(data, False)
        data = self.fixture()
        data.remove((EX.view, RAW.hasColumn, EX.column))
        data.add((Literal("invalid view"), RAW.hasColumn, EX.column))
        self.assert_valid(data, False)

    def test_mapped_predicate_cannot_replace_a_source_column_link(self):
        data = self.fixture()
        data.remove((EX.value, RAW.forColumn, None))
        data.add((EX.value, RAW.forPredicate, EX.identifier))
        data.add((EX.column, RAW.predicate, EX.identifier))
        self.assert_valid(data, False)

    def test_columns_with_the_same_mapping_keep_separate_locations(self):
        data = self.fixture()
        data.add((EX.column, RAW.predicate, EX.identifier))
        data.add((EX.otherColumn, RAW.predicate, EX.identifier))
        data.add((EX.view, RAW.hasColumn, EX.otherColumn))
        data.add((EX.otherValue, RAW.valueOf, EX.row))
        data.add((EX.otherValue, RAW.forColumn, EX.otherColumn))
        data.add((EX.otherValue, RAW.literalValue, Literal("another value")))
        self.assert_valid(data)
        self.assertEqual(list(data.query('''
            SELECT ?column WHERE {
                <https://example.test/value>
                    <https://ekgf.org/ontology/raw#forColumn> ?column .
            }
        ''')), [(EX.column,)])
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((EX.column, OWL.sameAs, EX.otherColumn), graph)
        self.assertNotIn((EX.value, OWL.sameAs, EX.otherValue), graph)

    def test_one_column_can_contain_values_from_multiple_rows(self):
        data = self.fixture()
        data.add((EX.otherRow, RAW.isRowInView, EX.view))
        data.add((EX.otherValue, RAW.valueOf, EX.otherRow))
        data.add((EX.otherValue, RAW.forColumn, EX.column))
        data.add((EX.otherValue, RAW.literalValue, Literal("other row")))
        self.assert_valid(data)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((EX.row, OWL.sameAs, EX.otherRow), graph)

    def test_null_occurrences_also_require_a_location(self):
        data = self.fixture()
        data.remove((EX.value, RAW.literalValue, None))
        data.add((EX.value, RDF.type, RAW.NullValue))
        self.assert_valid(data)
        data.remove((EX.value, RAW.forColumn, None))
        self.assert_valid(data, False)

    def test_blank_node_locations_are_supported(self):
        data = Graph()
        replacements = {node: BNode() for node in (EX.value, EX.row, EX.column, EX.view)}
        for subject, predicate, obj in self.fixture():
            data.add((replacements.get(subject, subject), predicate,
                      replacements.get(obj, obj)))
        self.assert_valid(data)

    def test_untyped_column_links_also_require_captured_content(self):
        data = self.fixture()
        data.remove((EX.value, RAW.literalValue, None))
        self.assert_valid(data, False)

    def test_row_and_column_subclasses_cannot_bypass_membership(self):
        for parent in (RAW.Row, RAW.Column):
            with self.subTest(parent=parent):
                data = Graph()
                data.add((EX.specialKind, RDFS.subClassOf, parent))
                data.add((EX.orphan, RDF.type, EX.specialKind))
                self.assert_valid(data, False)

    def test_location_shapes_pass_standard_shacl_meta_validation(self):
        self.assert_valid(self.fixture(), meta_shacl=True)

    def test_documented_capture_example_validates_with_all_shapes(self):
        text = (ROOT / "docs/raw-data.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data)
        values = set(data.subjects(RAW.literalValue, None))
        values.update(data.subjects(RDF.type, RAW.NullValue))
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(len(set(data.objects(value, RAW.valueOf))), 1)
                self.assertEqual(len(set(data.objects(value, RAW.forColumn))), 1)


if __name__ == "__main__":
    unittest.main()
