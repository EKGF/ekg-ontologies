"""Data element concepts retain their identity across uses and manifestations."""

import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, SKOS

from test_governance_registry import ERROR, EX, ROOT, turtle


CONCEPT = Namespace("https://ekgf.org/ontology/concept#")
STORY = Namespace("https://ekgf.org/ontology/story#")
USE_CASE = Namespace("https://ekgf.org/ontology/use-case#")
LIFECYCLE = Namespace("https://ekgf.org/ontology/lifecycle#")
SH = Namespace("http://www.w3.org/ns/shacl#")


class DataElementConceptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontologies = Graph()
        for name in ("concept", "persona", "story", "use-case"):
            cls.ontologies += turtle(f"ekgf-{name}.ttl")

    def reason(self, data):
        graph = self.ontologies + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def test_formal_class_has_one_shared_definition(self):
        self.assertIn((CONCEPT.DataElementConcept, RDF.type, OWL.Class),
                      self.ontologies)
        self.assertEqual(
            set(self.ontologies.objects(CONCEPT.DataElementConcept, RDFS.label)),
            {Literal("data element concept", lang="en")},
        )
        self.assertEqual(
            len(set(self.ontologies.objects(CONCEPT.DataElementConcept, RDFS.comment))),
            1,
        )

    def test_retired_class_is_absent_from_all_rdf_sources(self):
        for path in sorted(ROOT.rglob("*.ttl")):
            with self.subTest(path=path.relative_to(ROOT)):
                graph = Graph().parse(path, format="turtle")
                references = [triple for triple in graph if CONCEPT.Concept in triple]
                self.assertFalse(references, references)

    def test_story_use_case_and_manifestation_links_infer_the_new_class(self):
        data = Graph()
        links = (
            (EX.input, (EX.story, STORY.hasInputConcept, EX.input)),
            (EX.output, (EX.story, STORY.hasOutputConcept, EX.output)),
            (EX.dependency, (EX.story, STORY.hasDependentConcept, EX.dependency)),
            (EX.parameterConcept, (EX.parameter, CONCEPT.hasConcept, EX.parameterConcept)),
            (EX.used, (EX.useCase, USE_CASE.usesConcept, EX.used)),
            (EX.member, (EX.member, CONCEPT.inConceptSet, EX.conceptSet)),
            (EX.manifested, (EX.manifestation, CONCEPT.concept, EX.manifested)),
        )
        for _, triple in links:
            data.add(triple)
        graph = self.reason(data)
        for concept, _ in links:
            with self.subTest(concept=concept):
                self.assertIn((concept, RDF.type, CONCEPT.DataElementConcept), graph)
        self.assertIn((EX.conceptSet, RDF.type, CONCEPT.ConceptSet), graph)
        self.assertIn((EX.manifested, CONCEPT.hasManifestation, EX.manifestation), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_reused_concept_is_not_a_skos_concept_or_its_manifestations(self):
        data = Graph()
        data.add((EX.firstUseCase, USE_CASE.usesConcept, EX.customer))
        data.add((EX.secondUseCase, USE_CASE.usesConcept, EX.customer))
        data.add((EX.customer, CONCEPT.preferredBusinessTerm, EX.customerTerm))
        data.add((EX.customerTerm, RDF.type, CONCEPT.BusinessTerm))
        data.add((EX.customerTerm, RDFS.label, Literal("Customer", lang="en")))
        manifestations = (
            (EX.owlManifestation, CONCEPT.OWLClassManifestation, EX.Customer, OWL.Class),
            (EX.shapeManifestation, CONCEPT.SHACLShapeManifestation, EX.CustomerShape, SH.NodeShape),
            (EX.skosManifestation, CONCEPT.SKOSConceptManifestation, EX.customerSKOS, SKOS.Concept),
        )
        for manifestation, kind, resource, resource_type in manifestations:
            data.add((EX.customer, CONCEPT.hasManifestation, manifestation))
            data.add((manifestation, RDF.type, kind))
            data.add((manifestation, CONCEPT.manifestationResource, resource))
            data.add((resource, RDF.type, resource_type))
        graph = self.reason(data)
        self.assertNotIn((EX.customer, RDF.type, SKOS.Concept), graph)
        self.assertIn((EX.customer, RDF.type, CONCEPT.DataElementConcept), graph)
        self.assertNotIn((EX.customer, RDF.type, CONCEPT.ConceptManifestation), graph)
        self.assertIn((EX.customer, CONCEPT.hasManifestation, EX.customerTerm), graph)
        for manifestation, _, resource, resource_type in manifestations:
            with self.subTest(manifestation=manifestation):
                self.assertIn((manifestation, CONCEPT.concept, EX.customer), graph)
                self.assertIn((resource, RDF.type, resource_type), graph)
                self.assertNotIn((EX.customer, RDF.type, resource_type), graph)
                self.assertNotIn((resource, RDF.type, CONCEPT.DataElementConcept), graph)
                self.assertNotIn((EX.customer, OWL.sameAs, resource), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_new_class_keeps_the_continuous_improvement_lifecycle(self):
        bindings = turtle("dataset/lifecycle-bindings.ttl")
        self.assertIn((
            URIRef("https://ekgf.org/lifecycle/continuous-improvement"),
            LIFECYCLE.appliesTo,
            CONCEPT.DataElementConcept,
        ), bindings)

    def test_new_class_remains_disjoint_from_stories_and_use_cases(self):
        for other_class in (STORY.Story, USE_CASE.UseCase):
            with self.subTest(other_class=other_class):
                data = Graph()
                data.add((EX.conflict, RDF.type, CONCEPT.DataElementConcept))
                data.add((EX.conflict, RDF.type, other_class))
                self.assertTrue(list(self.reason(data).objects(None, ERROR)),
                                "Expected the existing class disjointness to apply")


if __name__ == "__main__":
    unittest.main()
