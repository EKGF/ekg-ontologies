"""Every ontology publishes a reusable SHACL mapping for its own namespace."""

import unittest

from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL, XSD

from test_governance_registry import EX, ROOT


SH = Namespace("http://www.w3.org/ns/shacl#")


class NamespaceDeclarationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontologies = []
        for path in sorted(ROOT.rglob("*.ttl")):
            graph = Graph(bind_namespaces="none").parse(path, format="turtle")
            for ontology in graph.subjects(RDF.type, OWL.Ontology):
                cls.ontologies.append((path, graph, ontology))

    def own_declaration(self, graph, ontology):
        namespace = Literal(str(ontology).removesuffix("#") + "#", datatype=XSD.anyURI)
        declarations = [
            node for node in graph.objects(ontology, SH.declare)
            if (node, SH.namespace, namespace) in graph
        ]
        self.assertEqual(len(declarations), 1,
                         f"Expected one declaration for {namespace} on {ontology}")
        return declarations[0]

    def test_every_ontology_declares_its_own_namespace_and_turtle_prefix(self):
        self.assertTrue(self.ontologies)
        for path, graph, ontology in self.ontologies:
            with self.subTest(path=path.name):
                declaration = self.own_declaration(graph, ontology)
                prefixes = list(graph.objects(declaration, SH.prefix))
                self.assertEqual(len(prefixes), 1)
                expected_prefix = {
                    "ekgf-artifact-governance": "ekg-artgov",
                    "ekgf-artifact-dependency": "ekg-artdep",
                    "ekgf-artifact-publication": "ekg-artpub",
                    "ekgf-maturity-model": "ekg-mm",
                    "ekgf-specification-by-example": "ekg-sbe",
                    "ekgf-user-experience": "ekg-ux",
                }.get(path.stem, "ekg-" + path.stem.removeprefix("ekgf-"))
                self.assertEqual(str(prefixes[0]), expected_prefix)
                namespace = graph.value(declaration, SH.namespace)
                self.assertEqual(dict(graph.namespaces()).get(str(prefixes[0])),
                                 URIRef(str(namespace)))

    def test_declarations_are_well_formed_and_prefixes_do_not_conflict(self):
        bindings = {}
        for path, graph, ontology in self.ontologies:
            with self.subTest(path=path.name):
                declarations = list(graph.objects(ontology, SH.declare))
                self.assertTrue(declarations)
                for declaration in declarations:
                    self.assertIsInstance(declaration, (BNode, URIRef))
                    prefixes = list(graph.objects(declaration, SH.prefix))
                    namespaces = list(graph.objects(declaration, SH.namespace))
                    self.assertEqual(len(prefixes), 1)
                    self.assertEqual(len(namespaces), 1)
                    prefix, namespace = prefixes[0], namespaces[0]
                    self.assertIsInstance(prefix, Literal)
                    self.assertIsNone(prefix.language)
                    self.assertIn(prefix.datatype, (None, XSD.string))
                    self.assertTrue(str(prefix))
                    self.assertNotIn(":", str(prefix))
                    self.assertIsInstance(namespace, Literal)
                    self.assertEqual(namespace.datatype, XSD.anyURI)
                    self.assertEqual(bindings.setdefault(str(prefix), namespace), namespace,
                                     f"Conflicting namespace for {prefix}")

    def test_shacl_sparql_can_use_each_ontology_declaration(self):
        for path, graph, ontology in self.ontologies:
            with self.subTest(path=path.name):
                declaration = self.own_declaration(graph, ontology)
                prefix = graph.value(declaration, SH.prefix)
                namespace = graph.value(declaration, SH.namespace)
                shapes = graph + Graph()
                constraint = BNode()
                shapes.add((EX.PrefixProbeShape, RDF.type, SH.NodeShape))
                shapes.add((EX.PrefixProbeShape, SH.targetNode, EX.probe))
                shapes.add((EX.PrefixProbeShape, SH.sparql, constraint))
                shapes.add((constraint, SH.prefixes, ontology))
                shapes.add((constraint, SH.select,
                            Literal(f"SELECT $this WHERE {{ $this a {prefix}:PrefixProbe }}")))
                data = Graph()
                data.add((EX.probe, RDF.type, URIRef(str(namespace) + "PrefixProbe")))
                conforms, report, _ = validate(data, shacl_graph=shapes)
                self.assertFalse(conforms)
                self.assertIn((None, SH.focusNode, EX.probe), report)
                self.assertIn((None, SH.sourceConstraintComponent, SH.SPARQLConstraintComponent), report)


if __name__ == "__main__":
    unittest.main()
