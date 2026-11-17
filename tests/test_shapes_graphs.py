"""Every ontology containing SHACL shapes is its own valid shapes graph."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Namespace, OWL, RDF


ROOT = Path(__file__).resolve().parents[1]
SH = Namespace("http://www.w3.org/ns/shacl#")


class ShapesGraphTests(unittest.TestCase):
    def shape_bearing_ontologies(self):
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path)
            if any(next(graph.subjects(RDF.type, kind), None) is not None
                   for kind in (SH.NodeShape, SH.PropertyShape)):
                yield path, graph

    def test_shape_bearing_ontologies_are_shapes_graphs(self):
        found = 0
        for path, graph in self.shape_bearing_ontologies():
            found += 1
            with self.subTest(path=path.name):
                ontology, = graph.subjects(RDF.type, OWL.Ontology)
                self.assertIn((ontology, RDF.type, SH.ShapesGraph), graph)
        self.assertGreater(found, 5)

    def test_shapes_pass_shacl_meta_validation(self):
        empty = Graph()
        for path, graph in self.shape_bearing_ontologies():
            with self.subTest(path=path.name):
                conforms, _, report = validate(empty, shacl_graph=graph, meta_shacl=True,
                                               do_owl_imports=False)
                self.assertTrue(conforms, report)


if __name__ == "__main__":
    unittest.main()
