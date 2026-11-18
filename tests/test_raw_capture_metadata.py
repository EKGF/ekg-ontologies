"""Raw capture metadata: file formats, view order, git origin and formulas."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, XSD


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")

COMMIT = "7cb0e12ad31958cab0cac1994784b5ccd90c8d8b"
BLOB = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
SHA256_COMMIT = "a" * 64

TERMS = {
    RAW.CsvFile: OWL.Class,
    RAW.TsvFile: OWL.Class,
    RAW.ParquetFile: OWL.Class,
    RAW.viewNumber: OWL.DatatypeProperty,
    RAW.gitRepository: OWL.DatatypeProperty,
    RAW.gitCommit: OWL.DatatypeProperty,
    RAW.gitPath: OWL.DatatypeProperty,
    RAW.gitBlob: OWL.DatatypeProperty,
    RAW.gitModified: OWL.DatatypeProperty,
    RAW.formula: OWL.DatatypeProperty,
    RAW.formulaR1C1: OWL.DatatypeProperty,
}


class RawCaptureMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True, shapes=None):
        # Fixtures omit rows, columns and views unless they are the subject;
        # formula cases therefore select the content and formula shapes.
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False, use_shapes=shapes,
        )
        self.assertEqual(conforms, expected, report)

    # -- vocabulary ---------------------------------------------------------

    def test_terms_are_declared_labelled_defined_and_owned(self):
        for term, kind in TERMS.items():
            with self.subTest(term=term):
                self.assertIn((term, RDF.type, kind), self.ontology)
                self.assertIn((term, RDFS.isDefinedBy, RAW[""]), self.ontology)
                self.assertTrue(list(self.ontology.objects(term, RDFS.label)))
                self.assertTrue(list(self.ontology.objects(term, RDFS.comment)))

    def test_file_formats_are_files(self):
        for cls in (RAW.CsvFile, RAW.TsvFile, RAW.ParquetFile):
            with self.subTest(cls=cls):
                self.assertIn((cls, RDFS.subClassOf, RAW.File), self.ontology)

    def test_shapes_are_in_the_ontology_shapes_graph(self):
        for shape in (RAW.ViewNumberShape, RAW.GitOriginShape, RAW.FormulaShape, RAW.FormulaR1C1Shape):
            with self.subTest(shape=shape):
                self.assertIn((shape, RDF.type, SH.NodeShape), self.ontology)

    # -- view number --------------------------------------------------------

    def view(self, *numbers):
        data = Graph()
        data.add((EX.view, RDF.type, RAW.View))
        for n in numbers:
            data.add((EX.view, RAW.viewNumber, n))
        return data

    def test_view_number_is_one_positive_integer(self):
        self.assert_valid(self.view(Literal(1)))
        self.assert_valid(self.view(Literal(0)), False)
        self.assert_valid(self.view(Literal("1")), False)
        self.assert_valid(self.view(Literal(1), Literal(2)), False)

    # -- git origin ---------------------------------------------------------

    def git_file(self, **props):
        data = Graph()
        data.add((EX.file, RDF.type, RAW.CsvFile))
        values = {
            "gitRepository": Literal("git@github.com:EKGF/ekg-lib.git"),
            "gitCommit": Literal(COMMIT),
            "gitPath": Literal("tests/data/people.csv"),
            "gitBlob": Literal(BLOB),
            "gitModified": Literal(False),
        }
        values.update(props)
        for name, value in values.items():
            if value is not None:
                data.add((EX.file, RAW[name], value))
        return data

    def test_complete_git_origin_is_valid(self):
        self.assert_valid(self.git_file())
        self.assert_valid(self.git_file(gitCommit=Literal(SHA256_COMMIT)))

    def test_repository_is_optional_but_commit_needs_path_and_state(self):
        self.assert_valid(self.git_file(gitRepository=None))
        self.assert_valid(self.git_file(gitPath=None), False)
        self.assert_valid(self.git_file(gitModified=None), False)

    def test_blob_alone_is_valid_outside_a_repository(self):
        data = Graph()
        data.add((EX.file, RDF.type, RAW.File))
        data.add((EX.file, RAW.gitBlob, Literal(BLOB)))
        self.assert_valid(data)

    def test_object_ids_are_lowercase_hex(self):
        self.assert_valid(self.git_file(gitCommit=Literal(COMMIT.upper())), False)
        self.assert_valid(self.git_file(gitBlob=Literal("not-a-hash")), False)

    def test_modified_is_boolean(self):
        self.assert_valid(self.git_file(gitModified=Literal("false")), False)

    def test_path_is_relative_and_slash_separated(self):
        self.assert_valid(self.git_file(gitPath=Literal("/abs/people.csv")), False)
        self.assert_valid(self.git_file(gitPath=Literal("tests\\people.csv")), False)

    # -- formulas -----------------------------------------------------------

    FORMULA_SHAPES = [RAW.ValueContentShape, RAW.FormulaShape, RAW.FormulaR1C1Shape]

    def assert_formula(self, data, expected=True):
        self.assert_valid(data, expected, self.FORMULA_SHAPES)

    def formula_value(self, **props):
        data = Graph()
        data.add((EX.value, RDF.type, RAW.Value))
        data.add((EX.value, RAW.literalValue, Literal(20.0)))
        for name, value in props.items():
            data.add((EX.value, RAW[name], value))
        return data

    def test_formula_value_keeps_cached_result_and_both_notations(self):
        self.assert_formula(self.formula_value(
            formula=Literal("A2*B2"), formulaR1C1=Literal("RC[-2]*RC[-1]"),
        ))

    def test_formula_without_cached_result_is_a_null_value(self):
        data = Graph()
        data.add((EX.value, RDF.type, RAW.NullValue))
        data.add((EX.value, RAW.formula, Literal("A2*B2")))
        self.assert_formula(data)

    def test_formula_is_a_single_string_on_a_value(self):
        self.assert_formula(self.formula_value(formula=Literal(1)), False)
        data = self.formula_value(formula=Literal("A2"))
        data.add((EX.value, RAW.formula, Literal("B2")))
        self.assert_formula(data, False)
        column = Graph()
        column.add((EX.column, RDF.type, RAW.Column))
        column.add((EX.column, RAW.formula, Literal("A2*B2")))
        self.assert_formula(column, False)

    def test_formula_text_excludes_the_leading_equals_sign(self):
        self.assert_formula(self.formula_value(formula=Literal("=A2*B2")), False)

    def test_column_may_carry_one_shared_r1c1_rule(self):
        column = Graph()
        column.add((EX.column, RDF.type, RAW.Column))
        column.add((EX.column, RAW.formulaR1C1, Literal("RC[-2]*RC[-1]")))
        self.assert_formula(column)
        column.add((EX.column, RAW.formulaR1C1, Literal("RC[-1]")))
        self.assert_formula(column, False)

    def test_r1c1_is_only_for_values_and_columns(self):
        data = Graph()
        data.add((EX.view, RDF.type, RAW.View))
        data.add((EX.view, RAW.formulaR1C1, Literal("RC")))
        self.assert_formula(data, False)


if __name__ == "__main__":
    unittest.main()
