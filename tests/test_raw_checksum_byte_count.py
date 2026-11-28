"""Raw checksums limited to the leading bytes of a file."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, XSD


ROOT = Path(__file__).resolve().parents[1]
RAW = Namespace("https://ekgf.org/ontology/raw#")
SPDX = Namespace("http://spdx.org/rdf/terms#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")

SHA256 = "1381aaec6311416fdde90cc217218c0cd8edf0afa6fa28d76b036055a8c3355b"


class ChecksumByteCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-raw.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
            use_shapes=[RAW.ChecksumByteCountShape],
        )
        self.assertEqual(conforms, expected, report)

    def checksum(self, *counts, value=True, algorithm=True):
        data = Graph()
        c = BNode()
        data.add((EX.output, SPDX.checksum, c))
        data.add((c, RDF.type, SPDX.Checksum))
        if value:
            data.add((c, SPDX.checksumValue, Literal(SHA256, datatype=XSD.hexBinary)))
        if algorithm:
            data.add((c, SPDX.algorithm, SPDX.checksumAlgorithm_sha256))
        for n in counts:
            data.add((c, RAW.checksumByteCount, n))
        return data

    def test_term_is_declared_labelled_defined_and_owned(self):
        term = RAW.checksumByteCount
        self.assertIn((term, RDF.type, OWL.DatatypeProperty), self.ontology)
        self.assertIn((term, RDF.type, OWL.FunctionalProperty), self.ontology)
        self.assertIn((term, RDFS.range, XSD.nonNegativeInteger), self.ontology)
        self.assertIn((term, RDFS.isDefinedBy, RAW[""]), self.ontology)
        self.assertTrue(list(self.ontology.objects(term, RDFS.label)))
        self.assertTrue(list(self.ontology.objects(term, RDFS.comment)))
        self.assertIn((RAW.ChecksumByteCountShape, RDF.type, SH.NodeShape), self.ontology)

    def test_one_non_negative_count_with_value_and_algorithm_is_valid(self):
        self.assert_valid(self.checksum(Literal(51, datatype=XSD.nonNegativeInteger)))

    def test_count_is_one_non_negative_integer(self):
        self.assert_valid(self.checksum(Literal("51")), False)
        self.assert_valid(self.checksum(Literal(51)), False)
        self.assert_valid(self.checksum(
            Literal(51, datatype=XSD.nonNegativeInteger),
            Literal(52, datatype=XSD.nonNegativeInteger)), False)

    def test_count_needs_the_value_and_algorithm_to_verify(self):
        n = Literal(51, datatype=XSD.nonNegativeInteger)
        self.assert_valid(self.checksum(n, value=False), False)
        self.assert_valid(self.checksum(n, algorithm=False), False)


if __name__ == "__main__":
    unittest.main()
