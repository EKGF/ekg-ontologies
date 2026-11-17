"""Column profiles: exact counts, an evidenced datatype, and statistics."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, XSD


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")

COUNTS = ("count", "nullCount", "unique", "freq", "conformingCount")
DOUBLES = ("mean", "std", "25pct", "50pct", "75pct")
PROFILE = COUNTS + DOUBLES + ("top", "min", "max", "inferredDatatype")


def d(value):
    return Literal(value, datatype=XSD.double)


class RawColumnProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        # A profile is validated on its own; column location is covered by
        # the location suite.
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
            use_shapes=[RAW.ColumnProfileShape],
        )
        self.assertEqual(conforms, expected, report)

    def column(self, **props):
        data = Graph()
        data.add((EX.column, RDF.type, RAW.Column))
        values = {
            "count": Literal(10), "nullCount": Literal(2),
            "unique": Literal(8), "top": Literal("2026-01-31"),
            "freq": Literal(3),
            "inferredDatatype": XSD.integer, "conformingCount": Literal(9),
            "min": Literal(1), "max": Literal(40),
            "mean": d(12.5), "std": d(4.0),
            "25pct": d(5.0), "50pct": d(11.0), "75pct": d(20.0),
        }
        values.update(props)
        for name, value in values.items():
            if value is not None:
                data.add((EX.column, RAW[name], value))
        return data

    # -- vocabulary ---------------------------------------------------------

    def test_profile_terms_are_functional_owned_and_defined(self):
        for name in PROFILE:
            term = RAW[name]
            with self.subTest(term=name):
                self.assertIn((term, RDF.type, OWL.FunctionalProperty), self.ontology)
                self.assertIn((term, RDFS.domain, RAW.Column), self.ontology)
                self.assertIn((term, RDFS.isDefinedBy, RAW[""]), self.ontology)
                self.assertEqual(len(list(self.ontology.objects(term, RDFS.label))), 1)
                self.assertEqual(len(list(self.ontology.objects(term, RDFS.comment))), 1)

    def test_profile_terms_have_precise_ranges(self):
        for name in COUNTS:
            self.assertIn((RAW[name], RDFS.range, XSD.integer), self.ontology)
        for name in DOUBLES:
            self.assertIn((RAW[name], RDFS.range, XSD.double), self.ontology)
        for name in ("top", "min", "max"):
            self.assertIn((RAW[name], RDFS.range, RDFS.Literal), self.ontology)
        self.assertIn((RAW.inferredDatatype, RDF.type, OWL.ObjectProperty), self.ontology)
        self.assertIn((RAW.inferredDatatype, RDFS.range, RDFS.Datatype), self.ontology)

    def test_profile_terms_no_longer_defer_to_pandas(self):
        for name in PROFILE:
            with self.subTest(term=name):
                self.assertEqual(list(self.ontology.objects(RAW[name], RDFS.seeAlso)), [])

    def test_profile_shape_is_a_node_shape(self):
        self.assertIn((RAW.ColumnProfileShape, RDF.type, SH.NodeShape), self.ontology)

    # -- valid profiles -----------------------------------------------------

    def test_complete_numeric_profile_is_valid(self):
        self.assert_valid(self.column())

    def test_counts_alone_are_valid(self):
        data = Graph()
        data.add((EX.column, RDF.type, RAW.Column))
        data.add((EX.column, RAW["count"], Literal(0)))
        data.add((EX.column, RAW.nullCount, Literal(0)))
        self.assert_valid(data)

    def test_date_profile_has_typed_extremes_and_no_moments(self):
        self.assert_valid(self.column(
            inferredDatatype=XSD.date,
            min=Literal("2020-01-01", datatype=XSD.date),
            max=Literal("2026-12-31", datatype=XSD.date),
            mean=None, std=None, **{"25pct": None, "50pct": None, "75pct": None},
        ))

    # -- invalid profiles ---------------------------------------------------

    def test_counts_are_non_negative_integers(self):
        for name in COUNTS:
            with self.subTest(term=name):
                self.assert_valid(self.column(**{name: Literal(-1)}), False)
                self.assert_valid(self.column(**{name: Literal("3")}), False)

    def test_statistics_are_doubles(self):
        for name in DOUBLES:
            with self.subTest(term=name):
                self.assert_valid(self.column(**{name: Literal(5)}), False)

    def test_each_measure_is_single_valued(self):
        data = self.column()
        data.add((EX.column, RAW["count"], Literal(11)))
        self.assert_valid(data, False)

    def test_counts_never_exceed_the_value_count(self):
        for name in ("unique", "freq", "conformingCount"):
            with self.subTest(term=name):
                self.assert_valid(self.column(**{name: Literal(11)}), False)

    def test_datatype_and_evidence_come_together(self):
        self.assert_valid(self.column(conformingCount=None), False)
        self.assert_valid(self.column(
            inferredDatatype=None, min=None, max=None, mean=None, std=None,
            **{"25pct": None, "50pct": None, "75pct": None},
        ), False)

    def test_top_and_freq_come_together(self):
        self.assert_valid(self.column(freq=None), False)
        self.assert_valid(self.column(top=None), False)

    def test_statistics_require_an_inferred_datatype(self):
        self.assert_valid(self.column(inferredDatatype=None, conformingCount=None), False)

    def test_extremes_and_percentiles_are_ordered(self):
        self.assert_valid(self.column(min=Literal(50)), False)
        self.assert_valid(self.column(**{"25pct": d(15.0)}), False)
        self.assert_valid(self.column(**{"75pct": d(41.0)}), False)


if __name__ == "__main__":
    unittest.main()
