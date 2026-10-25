"""Story implementations have one owner in each validated version context."""

from pathlib import Path
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import OWL


ROOT = Path(__file__).resolve().parents[1]
STORY = Namespace("https://ekgf.org/ontology/story#")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


class StoryImplementationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-story.ttl", format="turtle")

    def reason(self, data):
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def assert_valid(self, data, expected=True, inference="rdfs"):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference=inference,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self):
        graph = Graph()
        graph.add((EX.story, RDF.type, STORY.Story))
        graph.add((EX.implementation, RDF.type, STORY.StoryImplementation))
        return graph

    def test_canonical_relationship_infers_its_inverse_and_endpoint_types(self):
        for assertion, inverse in (
            ((EX.story, STORY.implementedBy, EX.implementation),
             (EX.implementation, STORY.implementationOf, EX.story)),
            ((EX.implementation, STORY.implementationOf, EX.story),
             (EX.story, STORY.implementedBy, EX.implementation)),
        ):
            with self.subTest(assertion=assertion):
                data = Graph()
                data.add(assertion)
                graph = self.reason(data)
                self.assertIn(inverse, graph)
                self.assertIn((EX.story, RDF.type, STORY.Story), graph)
                self.assertIn((EX.implementation, RDF.type,
                               STORY.StoryImplementation), graph)
                self.assertFalse(list(graph.objects(None, ERROR)))

    def test_one_story_can_have_zero_or_several_distinct_implementations(self):
        data = Graph()
        data.add((EX.story, RDF.type, STORY.Story))
        self.assert_valid(data)
        for implementation in (EX.firstImplementation, EX.secondImplementation):
            data.add((EX.story, STORY.implementedBy, implementation))
        data.add((EX.firstImplementation, OWL.differentFrom,
                  EX.secondImplementation))
        self.assert_valid(data)
        graph = self.reason(data)
        self.assertNotIn((EX.firstImplementation, OWL.sameAs,
                          EX.secondImplementation), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_owl_rejects_two_explicitly_distinct_owners(self):
        data = Graph()
        data.add((EX.firstStory, STORY.implementedBy, EX.implementation))
        data.add((EX.secondStory, STORY.implementedBy, EX.implementation))
        data.add((EX.firstStory, OWL.differentFrom, EX.secondStory))
        self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_forward_inverse_and_repeated_owner_assertions_are_valid(self):
        assertions = (
            (EX.story, STORY.implementedBy, EX.implementation),
            (EX.implementation, STORY.implementationOf, EX.story),
        )
        for selected in ((assertions[0],), (assertions[1],), assertions):
            with self.subTest(assertions=selected):
                data = self.fixture()
                for triple in selected:
                    data.add(triple)
                self.assert_valid(data)

    def test_missing_owner_is_rejected_for_base_class_and_subclasses(self):
        for kind in (STORY.StoryImplementation, STORY.NamedStatementImplementation,
                     STORY.ApiProxyImplementation, STORY.WorkflowImplementation,
                     STORY.AgentJobImplementation):
            with self.subTest(kind=kind):
                data = Graph()
                data.add((EX.implementation, RDF.type, kind))
                self.assert_valid(data, False)

    def test_implementation_metadata_cannot_bypass_missing_owner_validation(self):
        data = Graph()
        data.add((EX.implementation, STORY.implementationType, Literal("NamedStatement")))
        self.assert_valid(data, False, inference="none")

    def test_multiple_owners_are_rejected_in_either_or_both_directions(self):
        for first_forward, second_forward in ((True, True), (False, False),
                                              (True, False)):
            with self.subTest(first_forward=first_forward, second_forward=second_forward):
                data = self.fixture()
                data.remove((EX.implementation, RDF.type, None))
                data.add((EX.otherStory, RDF.type, STORY.Story))
                for owner, forward in ((EX.story, first_forward),
                                       (EX.otherStory, second_forward)):
                    data.add((owner, STORY.implementedBy, EX.implementation)
                             if forward else
                             (EX.implementation, STORY.implementationOf, owner))
                # Predicate targets must enforce ownership before type inference.
                self.assert_valid(data, False, inference="none")

    def test_rdfs_inference_accepts_relationships_without_explicit_endpoint_types(self):
        for assertion in (
            (EX.story, STORY.implementedBy, EX.implementation),
            (EX.implementation, STORY.implementationOf, EX.story),
        ):
            with self.subTest(assertion=assertion):
                data = Graph()
                data.add(assertion)
                self.assert_valid(data)

    def test_literal_owner_or_implementation_is_rejected(self):
        for assertion in (
            (EX.implementation, STORY.implementationOf, Literal("owner")),
            (EX.story, STORY.implementedBy, Literal("implementation")),
        ):
            with self.subTest(assertion=assertion):
                data = self.fixture()
                data.add(assertion)
                self.assert_valid(data, False)

    def test_retired_has_implementation_is_rejected_even_with_a_canonical_link(self):
        self.assertNotIn((STORY.hasImplementation, RDF.type, OWL.ObjectProperty),
                         self.ontology)
        for with_canonical in (False, True):
            with self.subTest(with_canonical=with_canonical):
                data = self.fixture()
                data.add((EX.story, STORY.hasImplementation, EX.implementation))
                if with_canonical:
                    data.add((EX.story, STORY.implementedBy, EX.implementation))
                self.assert_valid(data, False)

    def test_snapshot_scope_and_repeated_story_identity(self):
        for same_story in (False, True):
            with self.subTest(same_story=same_story):
                dataset = Dataset()
                merged = Graph()
                for name, owner in ((EX.firstSnapshot, EX.firstStory),
                                    (EX.secondSnapshot,
                                     EX.firstStory if same_story else EX.secondStory)):
                    snapshot = dataset.graph(name)
                    snapshot.add((owner, RDF.type, STORY.Story))
                    snapshot.add((EX.implementation, RDF.type, STORY.StoryImplementation))
                    snapshot.add((EX.implementation, STORY.implementationOf, owner))
                    self.assert_valid(snapshot)
                    merged += snapshot
                self.assert_valid(merged, same_story)


if __name__ == "__main__":
    unittest.main()
