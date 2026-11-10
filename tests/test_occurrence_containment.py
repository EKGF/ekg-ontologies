"""Containment describes source occurrences independently of shared meanings."""

from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
CONCEPT = Namespace("https://ekgf.org/ontology/concept#")
STORY = Namespace("https://ekgf.org/ontology/story#")
SH = Namespace("http://www.w3.org/ns/shacl#")
META = Namespace("https://ekgf.org/ontology/shape#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


class OccurrenceContainmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")

    def fixture(self):
        data = Graph()
        for occurrence, manifestation in ((EX.child, EX.field), (EX.parent, EX.record)):
            data.add((occurrence, RDF.type, CONCEPT.ManifestationOccurrence))
            data.add((occurrence, CONCEPT.occurrenceOf, manifestation))
            data.add((manifestation, RDF.type, CONCEPT.TechnicalManifestation))
        data.add((EX.child, CONCEPT.occursWithin, EX.parent))
        return data

    def reason(self, data):
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def assert_valid(self, data, expected=True, inference="rdfs", **options):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference=inference, do_owl_imports=False, **options,
        )
        self.assertEqual(conforms, expected, report)

    def test_property_infers_occurrence_endpoints(self):
        data = Graph()
        data.add((EX.child, CONCEPT.occursWithin, EX.parent))
        graph = self.reason(data)
        for node in (EX.child, EX.parent):
            self.assertIn((node, RDF.type, CONCEPT.ManifestationOccurrence), graph)
            self.assertNotIn((node, RDF.type, CONCEPT.DataElementConcept), graph)
            self.assertNotIn((node, RDF.type, CONCEPT.ConceptManifestation), graph)
        self.assertIn((CONCEPT.occursWithin, RDF.type, OWL.ObjectProperty), self.ontology)
        self.assert_valid(data)

    def test_direct_links_do_not_materialize_ancestor_links(self):
        data = self.fixture()
        data.add((EX.parent, CONCEPT.occursWithin, EX.root))
        self.assert_valid(data)
        graph = self.reason(data)
        self.assertNotIn((CONCEPT.occursWithin, RDF.type, OWL.TransitiveProperty),
                         self.ontology)
        self.assertNotIn((EX.child, CONCEPT.occursWithin, EX.root), graph)
        rows = data.query("""
            PREFIX concept: <https://ekgf.org/ontology/concept#>
            PREFIX ex: <https://example.test/>
            SELECT ?container WHERE { ex:child concept:occursWithin+ ?container }
        """)
        self.assertEqual({row.container for row in rows}, {EX.parent, EX.root})

    def test_multiple_children_and_containers_keep_distinct_identities(self):
        data = self.fixture()
        data.add((EX.child, CONCEPT.occursWithin, EX.otherParent))
        data.add((EX.otherChild, CONCEPT.occursWithin, EX.parent))
        data.add((EX.parent, OWL.differentFrom, EX.otherParent))
        data.add((EX.child, OWL.differentFrom, EX.otherChild))
        self.assert_valid(data)
        graph = self.reason(data)
        for kind in (OWL.FunctionalProperty, OWL.InverseFunctionalProperty):
            self.assertNotIn((CONCEPT.occursWithin, RDF.type, kind), self.ontology)
        self.assertNotIn((EX.parent, OWL.sameAs, EX.otherParent), graph)
        self.assertNotIn((EX.child, OWL.sameAs, EX.otherChild), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_occurrences_without_a_container_remain_valid(self):
        data = self.fixture()
        data.remove((None, CONCEPT.occursWithin, None))
        self.assert_valid(data)

    def test_named_and_blank_occurrences_are_supported(self):
        for child, parent in ((EX.child, BNode()), (BNode(), EX.parent),
                              (BNode(), BNode())):
            with self.subTest(child=child, parent=parent):
                data = Graph()
                data.add((child, CONCEPT.occursWithin, parent))
                self.assert_valid(data)

    def test_literal_endpoints_are_rejected_even_without_explicit_types(self):
        for child, parent in ((Literal("child"), EX.parent),
                              (EX.child, Literal("parent"))):
            with self.subTest(child=child, parent=parent):
                data = Graph()
                data.add((child, CONCEPT.occursWithin, parent))
                self.assert_valid(data, False)

    def test_no_inference_validation_requires_supplied_occurrence_types(self):
        data = self.fixture()
        self.assert_valid(data, inference="none")
        for node in (EX.child, EX.parent):
            with self.subTest(node=node):
                incomplete = Graph()
                incomplete += data
                incomplete.remove((node, RDF.type, CONCEPT.ManifestationOccurrence))
                self.assert_valid(incomplete, False, inference="none")

    def test_occurrence_subclasses_are_accepted(self):
        data = self.fixture()
        data.add((EX.FieldOccurrence, RDFS.subClassOf, CONCEPT.ManifestationOccurrence))
        data.set((EX.child, RDF.type, EX.FieldOccurrence))
        self.assert_valid(data)

    def test_concepts_and_manifestations_cannot_be_used_as_occurrences(self):
        for node in (EX.child, EX.parent):
            for kind in (CONCEPT.DataElementConcept, CONCEPT.ConceptManifestation,
                         CONCEPT.OWLPropertyManifestation):
                with self.subTest(node=node, kind=kind):
                    data = self.fixture()
                    data.add((node, RDF.type, kind))
                    self.assert_valid(data, False)
                    self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_cycles_are_rejected_without_materializing_transitive_links(self):
        for nodes in ((EX.child,), (EX.child, EX.parent),
                      (EX.child, EX.parent, EX.root)):
            with self.subTest(nodes=nodes):
                data = Graph()
                for index, node in enumerate(nodes):
                    data.add((node, RDF.type, CONCEPT.ManifestationOccurrence))
                    data.add((node, CONCEPT.occursWithin, nodes[(index + 1) % len(nodes)]))
                self.assert_valid(data, False, inference="none")
        self.assertIn((CONCEPT.occursWithin, RDF.type, OWL.IrreflexiveProperty),
                      self.ontology)

    def test_shared_manifestations_do_not_share_or_inherit_containers(self):
        data = self.fixture()
        data.add((EX.otherChild, CONCEPT.occurrenceOf, EX.field))
        data.add((EX.otherChild, CONCEPT.occursWithin, EX.otherParent))
        data.add((EX.fieldConcept, CONCEPT.hasManifestation, EX.field))
        data.add((EX.recordConcept, CONCEPT.hasManifestation, EX.record))
        self.assert_valid(data)
        graph = self.reason(data)
        for triple in (
            (EX.otherChild, CONCEPT.occursWithin, EX.parent),
            (EX.child, CONCEPT.occursWithin, EX.otherParent),
            (EX.field, CONCEPT.occursWithin, EX.record),
            (EX.fieldConcept, CONCEPT.occursWithin, EX.recordConcept),
        ):
            self.assertNotIn(triple, graph)
        self.assertNotIn((EX.child, OWL.sameAs, EX.otherChild), graph)

    def test_provenance_is_not_inherited_or_used_as_a_containment_key(self):
        data = self.fixture()
        data.add((EX.parent, CONCEPT.sourcePath, Literal("sources/records.xlsx")))
        data.add((EX.parent, CONCEPT.sourceSystem, EX.system))
        data.add((EX.otherChild, CONCEPT.sourcePath, Literal("sources/records.xlsx")))
        graph = self.reason(data)
        self.assertEqual(list(graph.objects(EX.child, CONCEPT.sourcePath)), [])
        self.assertEqual(list(graph.objects(EX.child, CONCEPT.sourceSystem)), [])
        self.assertEqual(list(graph.objects(EX.otherChild, CONCEPT.occursWithin)), [])
        self.assert_valid(data)

    def test_observations_do_not_create_story_concept_declarations(self):
        data = self.fixture()
        data.add((EX.fieldConcept, CONCEPT.hasManifestation, EX.field))
        graph = self.reason(data)
        for predicate in (STORY.hasInputConcept, STORY.hasOutputConcept,
                          STORY.hasDependentConcept, STORY.hasConceptUsage):
            self.assertEqual(list(graph.triples((None, predicate, None))), [])

    def test_validator_is_registered_and_meta_valid(self):
        self.assertIn((CONCEPT.ValidationShapeSet, META.hasShape,
                       CONCEPT.OccurrenceContainmentShape), self.ontology)
        self.assert_valid(self.fixture(), meta_shacl=True)

    def test_containment_terms_have_markdown_explanations(self):
        for term in (CONCEPT.occursWithin, CONCEPT.ManifestationOccurrence,
                     CONCEPT.OccurrenceContainmentShape):
            with self.subTest(term=term):
                self.assertTrue(any(
                    isinstance(value, Literal) and value.language == "en"
                    and len(str(value)) > 100
                    for value in self.ontology.objects(term, ANNOTATION.markdownDescription)
                ))

    def test_documented_observations_validate_and_link_attribute_to_compound_meaning(self):
        text = (ROOT / "docs/occurrence-containment.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data)
        query, = re.findall(r"```sparql\n(.*?)```", text, re.DOTALL)
        rows = list(data.query(query))
        self.assertEqual([(row.attributeConcept, row.compoundConcept) for row in rows],
                         [(EX.recordIdentifierConcept, EX.recordConcept)])


if __name__ == "__main__":
    unittest.main()
