"""Lifecycle history heads, permitted moves and multi-lifecycle assignments."""
from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, XSD

ROOT = Path(__file__).resolve().parents[1]
LC = Namespace("https://ekgf.org/ontology/lifecycle#")
EX = Namespace("https://example.test/")
PROV = Namespace("http://www.w3.org/ns/prov#")


class LifecycleHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-lifecycle.ttl")

    def assert_valid(self, graph, expected=True):
        conforms, _, report = validate(graph, shacl_graph=self.ontology)
        self.assertEqual(conforms, expected, report)

    def fixture(self):
        graph = Graph()
        graph.add((EX.lifecycle, RDF.type, LC.Lifecycle))
        for state in (EX.start, EX.finish):
            graph.add((state, RDF.type, LC.State))
            graph.add((state, LC.inLifecycle, EX.lifecycle))
        graph.add((EX.route, RDF.type, LC.Transition))
        graph.add((EX.route, LC.inLifecycle, EX.lifecycle))
        graph.add((EX.route, LC.fromState, EX.start))
        graph.add((EX.route, LC.toState, EX.finish))
        graph.add((EX.object, LC.followsLifecycle, EX.lifecycle))
        graph.add((EX.object, LC.inState, EX.latest))
        for occurrence, state in ((EX.first, EX.start), (EX.latest, EX.finish)):
            graph.add((occurrence, RDF.type, LC.StateTransition))
            graph.add((occurrence, LC.currentState, state))
        graph.add((EX.latest, LC.priorStateTransition, EX.first))
        return graph

    def test_vocabulary_replaces_direct_state_and_allows_multiple_lifecycles(self):
        self.assertNotIn((LC.hasState, RDF.type, OWL.ObjectProperty), self.ontology)
        self.assertNotIn((LC.followsLifecycle, RDF.type, OWL.FunctionalProperty), self.ontology)
        self.assertNotIn((LC.inState, RDF.type, OWL.FunctionalProperty), self.ontology)
        self.assertIn((LC.StateTransition, RDF.type, OWL.Class), self.ontology)
        for prop, target in ((LC.inState, LC.StateTransition),
                             (LC.currentState, LC.State),
                             (LC.priorStateTransition, LC.StateTransition)):
            self.assertIn((prop, RDFS.range, target), self.ontology)
        for prop in (LC.currentState, LC.priorStateTransition):
            self.assertIn((prop, RDF.type, OWL.FunctionalProperty), self.ontology)

    def test_valid_history_and_optional_provenance(self):
        graph = self.fixture()
        self.assert_valid(graph)
        graph.add((EX.latest, PROV.generatedAtTime,
                   Literal("2026-10-23T15:00:00Z", datatype=XSD.dateTime)))
        graph.add((EX.latest, PROV.wasAttributedTo, EX.editor))
        self.assert_valid(graph)

    def test_initial_occurrence_and_blank_node_head(self):
        graph = self.fixture()
        graph.remove((EX.latest, LC.priorStateTransition, None))
        head = BNode()
        for predicate, value in list(graph.predicate_objects(EX.latest)):
            graph.add((head, predicate, value))
        graph.remove((EX.latest, None, None))
        graph.set((EX.object, LC.inState, head))
        self.assert_valid(graph)

    def test_two_lifecycles_and_one_head_each(self):
        graph = self.fixture()
        graph.add((EX.otherLifecycle, RDF.type, LC.Lifecycle))
        graph.add((EX.otherState, RDF.type, LC.State))
        graph.add((EX.otherState, LC.inLifecycle, EX.otherLifecycle))
        graph.add((EX.otherHead, RDF.type, LC.StateTransition))
        graph.add((EX.otherHead, LC.currentState, EX.otherState))
        graph.add((EX.object, LC.followsLifecycle, EX.otherLifecycle))
        graph.add((EX.object, LC.inState, EX.otherHead))
        self.assert_valid(graph)

    def test_missing_head_or_unrelated_lifecycle_is_rejected(self):
        graph = self.fixture()
        graph.remove((EX.object, LC.inState, None))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.add((EX.otherLifecycle, RDF.type, LC.Lifecycle))
        graph.set((EX.object, LC.followsLifecycle, EX.otherLifecycle))
        self.assert_valid(graph, False)

    def test_class_defaults_and_explicit_override(self):
        graph = self.fixture()
        graph.remove((EX.object, LC.followsLifecycle, None))
        graph.add((EX.object, RDF.type, EX.Special))
        graph.add((EX.Special, RDFS.subClassOf, EX.Base))
        graph.add((EX.lifecycle, LC.appliesTo, EX.Base))
        self.assert_valid(graph)
        graph.remove((EX.object, LC.inState, None))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.add((EX.object, RDF.type, EX.Base))
        graph.add((EX.otherLifecycle, RDF.type, LC.Lifecycle))
        graph.add((EX.otherLifecycle, LC.appliesTo, EX.Base))
        self.assert_valid(graph)

    def test_duplicate_heads_for_one_lifecycle_are_rejected(self):
        graph = self.fixture()
        graph.add((EX.duplicate, RDF.type, LC.StateTransition))
        graph.add((EX.duplicate, LC.currentState, EX.finish))
        graph.add((EX.object, LC.inState, EX.duplicate))
        self.assert_valid(graph, False)

    def test_occurrence_cardinality_and_types(self):
        for prop in (LC.currentState, LC.priorStateTransition):
            graph = self.fixture()
            graph.add((EX.latest, prop, EX.extra))
            self.assert_valid(graph, False)
        graph = self.fixture()
        graph.remove((EX.first, LC.currentState, None))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.remove((EX.first, RDF.type, LC.StateTransition))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.remove((EX.finish, RDF.type, LC.State))
        self.assert_valid(graph, False)

    def test_missing_or_multiple_state_lifecycle_is_rejected(self):
        for multiple in (False, True):
            graph = self.fixture()
            if multiple:
                graph.add((EX.finish, LC.inLifecycle, EX.extra))
            else:
                graph.remove((EX.finish, LC.inLifecycle, None))
            self.assert_valid(graph, False)

    def test_cross_lifecycle_history_is_rejected(self):
        graph = self.fixture()
        graph.add((EX.otherLifecycle, RDF.type, LC.Lifecycle))
        graph.set((EX.start, LC.inLifecycle, EX.otherLifecycle))
        self.assert_valid(graph, False)

    def test_unpermitted_move_and_terminal_source_are_rejected(self):
        graph = self.fixture()
        graph.remove((EX.route, None, None))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.add((EX.start, LC.isTerminal, Literal(True)))
        self.assert_valid(graph, False)

    def test_cycles_in_history_are_rejected(self):
        graph = self.fixture()
        graph.add((EX.first, LC.priorStateTransition, EX.latest))
        self.assert_valid(graph, False)
        graph = self.fixture()
        graph.set((EX.latest, LC.priorStateTransition, EX.latest))
        self.assert_valid(graph, False)

    def test_permitted_state_loop_uses_distinct_occurrences(self):
        graph = self.fixture()
        graph.set((EX.route, LC.toState, EX.start))
        graph.set((EX.latest, LC.currentState, EX.start))
        self.assert_valid(graph)

    def test_different_objects_cannot_share_occurrences(self):
        graph = self.fixture()
        graph.add((EX.otherObject, LC.followsLifecycle, EX.lifecycle))
        graph.add((EX.otherHead, RDF.type, LC.StateTransition))
        graph.add((EX.otherHead, LC.currentState, EX.finish))
        graph.add((EX.otherHead, LC.priorStateTransition, EX.first))
        graph.add((EX.otherObject, LC.inState, EX.otherHead))
        self.assert_valid(graph, False)

    def test_head_with_recorded_successor_is_rejected(self):
        graph = self.fixture()
        graph.set((EX.object, LC.inState, EX.first))
        self.assert_valid(graph, False)

    def test_legacy_direct_state_is_rejected(self):
        graph = self.fixture()
        graph.add((EX.object, LC.hasState, EX.finish))
        self.assert_valid(graph, False)


if __name__ == "__main__":
    unittest.main()
