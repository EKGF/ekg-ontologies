"""Shape collections reference concrete validation graphs with separate identities."""

from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
META = Namespace("https://ekgf.org/ontology/shape#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
PROF = Namespace("http://www.w3.org/ns/dx/prof/")
USE_CASE = Namespace("https://ekgf.org/ontology/use-case#")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


class ShapesGraphLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-shape.ttl", format="turtle")

    def assert_valid(self, data, expected=True, **options):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            do_owl_imports=False, **options,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self, linked=True):
        data = Graph()
        data.add((EX.shapeset, RDF.type, META.ShapeSet))
        data.add((EX.shapeset, RDFS.label, Literal("Example validation set", lang="en")))
        data.add((EX.shapeset, META.shapePurpose, META.Validation))
        data.add((EX.shapeset, META.hasShape, EX.personShape))
        data.add((EX.personShape, RDF.type, SH.NodeShape))
        if linked:
            data.add((EX.shapeset, META.hasShapesGraph, EX.shapesGraph))
            data.add((EX.shapesGraph, RDF.type, SH.ShapesGraph))
        return data

    def test_links_infer_endpoint_roles_without_equating_their_identities(self):
        data = Graph()
        data.add((EX.shapeset, META.hasShapesGraph, EX.shapesGraph))
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertIn((EX.shapeset, RDF.type, META.ShapeSet), graph)
        self.assertIn((EX.shapesGraph, RDF.type, SH.ShapesGraph), graph)
        self.assertNotIn((EX.shapeset, OWL.sameAs, EX.shapesGraph), graph)
        self.assertNotIn((EX.shapeset, RDF.type, SH.ShapesGraph), graph)

    def test_graph_link_is_optional_and_does_not_materialize_a_default(self):
        data = self.fixture(linked=False)
        self.assert_valid(data, inplace=True)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(list(graph.objects(EX.shapeset, META.hasShapesGraph)), [])

    def test_a_set_can_reference_several_graphs_and_graphs_can_serve_several_sets(self):
        data = self.fixture()
        data.add((EX.shapeset, META.hasShapesGraph, EX.otherGraph))
        data.add((EX.otherGraph, RDF.type, SH.ShapesGraph))
        data.add((EX.otherSet, RDF.type, META.ShapeSet))
        data.add((EX.otherSet, RDFS.label, Literal("Other set", lang="en")))
        data.add((EX.otherSet, META.shapePurpose, META.Validation))
        data.add((EX.otherSet, META.hasShape, EX.personShape))
        data.add((EX.otherSet, META.hasShapesGraph, EX.shapesGraph))
        self.assert_valid(data)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((EX.shapesGraph, OWL.sameAs, EX.otherGraph), graph)
        self.assertNotIn((EX.shapeset, OWL.sameAs, EX.otherSet), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_graph_endpoints_require_typed_iris(self):
        for node in (BNode(), Literal("shapes.ttl"), EX.untypedGraph):
            with self.subTest(node=node):
                data = self.fixture(linked=False)
                data.add((EX.shapeset, META.hasShapesGraph, node))
                if node != EX.untypedGraph:
                    data.add((node, RDF.type, SH.ShapesGraph))
                self.assert_valid(data, False)

    def test_link_subjects_must_be_complete_shapesets(self):
        for missing in (RDF.type, RDFS.label, META.hasShape, META.shapePurpose):
            with self.subTest(missing=missing):
                data = self.fixture()
                data.remove((EX.shapeset, missing, None))
                self.assert_valid(data, False)
        for node in (BNode(), Literal("not a set")):
            with self.subTest(node=node):
                data = Graph()
                for subject, predicate, obj in self.fixture():
                    data.add((node if subject == EX.shapeset else subject, predicate, obj))
                self.assert_valid(data, False)

    def test_set_and_graph_roles_are_disjoint_even_without_a_link(self):
        data = self.fixture(linked=False)
        data.add((EX.shapeset, RDF.type, SH.ShapesGraph))
        self.assert_valid(data, False)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertTrue(list(graph.objects(None, ERROR)))

    def test_self_links_and_links_to_another_shapeset_are_rejected(self):
        for same_set in (False, True):
            with self.subTest(same_set=same_set):
                data = self.fixture(linked=False)
                node = EX.shapeset if same_set else EX.otherSet
                if not same_set:
                    data.add((node, RDF.type, META.ShapeSet))
                    data.add((node, RDFS.label, Literal("Other set", lang="en")))
                    data.add((node, META.shapePurpose, META.Validation))
                    data.add((node, META.hasShape, EX.personShape))
                data.add((node, RDF.type, SH.ShapesGraph))
                data.add((EX.shapeset, META.hasShapesGraph, node))
                self.assert_valid(data, False)

    def test_graph_subclasses_are_supported(self):
        data = self.fixture()
        data.remove((EX.shapesGraph, RDF.type, SH.ShapesGraph))
        data.add((EX.versionedGraph, RDFS.subClassOf, SH.ShapesGraph))
        data.add((EX.shapesGraph, RDF.type, EX.versionedGraph))
        self.assert_valid(data)

    def test_link_alone_does_not_assert_conformance_or_load_graphs(self):
        data = self.fixture()
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        for predicate in (SH.shapesGraph, SH.conformsToShapesGraph,
                          URIRef("http://purl.org/dc/terms/conformsTo")):
            self.assertEqual(list(graph.triples((None, predicate, None))), [])

    def test_use_case_placement_creates_no_profile_or_graph_inheritance(self):
        data = self.fixture()
        data.add((EX.child, USE_CASE.isPartOf, EX.parent))
        data.add((EX.reused, USE_CASE.isUsedIn, EX.child))
        graph = self.ontology + data + Graph().parse(ROOT / "ekgf-use-case.ttl", format="turtle")
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        for predicate in (PROF.isProfileOf, SH.shapesGraph, SH.conformsToShapesGraph):
            self.assertEqual(list(graph.triples((None, predicate, None))), [])
        self.assertEqual(set(graph.subjects(META.hasShapesGraph, EX.shapesGraph)), {EX.shapeset})

    def test_repository_sets_bind_to_their_supplied_module_graphs(self):
        count = 0
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path, format="turtle")
            for shapeset in graph.subjects(RDF.type, META.ShapeSet):
                count += 1
                with self.subTest(path=path.name):
                    header, = graph.subjects(RDF.type, OWL.Ontology)
                    self.assertEqual(set(graph.objects(shapeset, META.hasShapesGraph)), {header})
                    self.assertNotEqual(shapeset, header)
                    self.assertIn((header, RDF.type, SH.ShapesGraph), graph)
                    concrete = Graph(identifier=header).parse(path, format="turtle")
                    self.assert_valid(concrete)
                    entries = set(graph.objects(shapeset, META.hasShape))
                    entries.update(graph.subjects(META.inShapeSet, shapeset))
                    self.assertTrue(entries)
                    for entry in entries:
                        self.assertTrue(list(concrete.triples((entry, None, None))))
        self.assertGreaterEqual(count, 8)

    def test_documentation_is_available_as_markdown_annotations(self):
        for term in (META.ShapeSet, META.hasShapesGraph, META.ShapesGraphLinkShape):
            with self.subTest(term=term):
                descriptions = list(self.ontology.objects(term, ANNOTATION.markdownDescription))
                self.assertTrue(descriptions)
                self.assertTrue(any(value.language == "en" and len(str(value)) > 100
                                    for value in descriptions))

    def test_metadata_constraints_pass_standard_shacl_meta_validation(self):
        self.assert_valid(self.fixture(), meta_shacl=True)

    def test_documented_graph_can_be_selected_for_actual_data_validation(self):
        text = (ROOT / "docs/shapes-graphs.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        concrete = Graph(identifier=EX.personShapesGraph).parse(data=example, format="turtle")
        self.assert_valid(concrete)
        selected, = concrete.objects(EX.personShapeSet, META.hasShapesGraph)
        self.assertEqual(selected, concrete.identifier)
        data = Graph()
        data.add((EX.person, RDF.type, EX.Person))
        conforms, _, _ = validate(data, shacl_graph=concrete, do_owl_imports=False)
        self.assertFalse(conforms)
        data.add((EX.person, EX.name, Literal("Example person")))
        conforms, _, _ = validate(data, shacl_graph=concrete, do_owl_imports=False)
        self.assertTrue(conforms)


if __name__ == "__main__":
    unittest.main()
