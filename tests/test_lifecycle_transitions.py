"""Explicit lifecycle routes and invalid transition rejection."""
from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parents[1]
LC = Namespace("https://ekgf.org/ontology/lifecycle#")
EX = Namespace("https://example.test/")


class LifecycleTransitionTests(unittest.TestCase):
    def setUp(self):
        self.ontology = Graph().parse(ROOT / "ekgf-lifecycle.ttl")
        self.registry = Graph().parse(ROOT / "dataset/well-known-lifecycles.ttl")

    def conforms(self, graph):
        return validate(graph, shacl_graph=self.ontology)[0]

    def fixture(self):
        graph = Graph()
        for state in (EX.source, EX.target):
            graph.add((state, RDF.type, LC.State))
            graph.add((state, LC.inLifecycle, EX.lifecycle))
        graph.add((EX.lifecycle, RDF.type, LC.Lifecycle))
        graph.add((EX.transition, RDF.type, LC.Transition))
        graph.add((EX.transition, LC.inLifecycle, EX.lifecycle))
        graph.add((EX.transition, LC.fromState, EX.source))
        graph.add((EX.transition, LC.toState, EX.target))
        return graph

    def test_transition_vocabulary(self):
        self.assertIn((LC.Transition, RDF.type, OWL.Class), self.ontology)
        for prop in (LC.fromState, LC.toState):
            self.assertIn((prop, RDF.type, OWL.FunctionalProperty), self.ontology)
            self.assertIn((prop, RDFS.domain, LC.Transition), self.ontology)
            self.assertIn((prop, RDFS.range, LC.State), self.ontology)
        self.assertIn((LC.trigger, RDF.type, OWL.DatatypeProperty), self.ontology)
        domain = self.ontology.value(LC.inLifecycle, RDFS.domain)
        members = self.ontology.value(domain, OWL.unionOf)
        self.assertIn(LC.Transition, list(self.ontology.items(members)))

    def test_registry_has_explicit_routes_for_every_lifecycle(self):
        transitions = set(self.registry.subjects(RDF.type, LC.Transition))
        self.assertTrue(transitions)
        self.assertTrue(self.conforms(self.registry))
        for lifecycle in self.registry.subjects(RDF.type, LC.Lifecycle):
            routes = {t for t in transitions if (t, LC.inLifecycle, lifecycle) in self.registry}
            self.assertTrue(routes, lifecycle)
            for transition in routes:
                self.assertIsInstance(transition, URIRef)
                self.assertIsNotNone(self.registry.value(transition, RDFS.label))
            # All registered states participate, including terminal alternatives.
            endpoints = {state for t in routes for p in (LC.fromState, LC.toState)
                         for state in self.registry.objects(t, p)}
            states = {s for s in self.registry.subjects(RDF.type, LC.State)
                      if (s, LC.inLifecycle, lifecycle) in self.registry}
            self.assertEqual(endpoints, states)

    def test_branches_and_loops_are_explicit(self):
        def has_route(slug, source, target):
            ns = Namespace(f"https://ekgf.org/lifecycle/{slug}#")
            return any((t, LC.toState, ns[target]) in self.registry
                       for t in self.registry.subjects(LC.fromState, ns[source]))
        for target in ("Done", "Failed", "Cancelled"):
            self.assertTrue(has_route("execution", "Running", target))
        self.assertFalse(has_route("execution", "Done", "Failed"))
        self.assertTrue(has_route("continuous-improvement", "Deprecated", "InProgress"))

    def test_valid_branch_loop_and_optional_trigger(self):
        graph = self.fixture()
        graph.add((EX.transition, LC.trigger, Literal("Review accepted", lang="en")))
        self.assertTrue(self.conforms(graph))
        graph.set((EX.transition, LC.toState, EX.source))
        self.assertTrue(self.conforms(graph))

    def test_missing_or_multiple_required_values_are_rejected(self):
        for prop in (LC.fromState, LC.toState, LC.inLifecycle):
            with self.subTest(prop=prop):
                graph = self.fixture()
                graph.remove((EX.transition, prop, None))
                self.assertFalse(self.conforms(graph))
                graph = self.fixture()
                graph.add((EX.transition, prop, EX.extra))
                self.assertFalse(self.conforms(graph))

    def test_cross_lifecycle_endpoints_are_rejected(self):
        for state in (EX.source, EX.target):
            with self.subTest(state=state):
                graph = self.fixture()
                graph.set((state, LC.inLifecycle, EX.otherLifecycle))
                self.assertFalse(self.conforms(graph))
                graph = self.fixture()
                graph.add((state, LC.inLifecycle, EX.otherLifecycle))
                self.assertFalse(self.conforms(graph))

    def test_terminal_source_is_rejected(self):
        graph = self.fixture()
        graph.add((EX.source, LC.isTerminal, Literal(True)))
        self.assertFalse(self.conforms(graph))


if __name__ == "__main__":
    unittest.main()
