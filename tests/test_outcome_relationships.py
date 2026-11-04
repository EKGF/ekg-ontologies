"""Use-case contributions have identities independent of their shared outcomes."""

from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Dataset, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
OUTCOME = Namespace("https://ekgf.org/ontology/outcome#")
USE_CASE = Namespace("https://ekgf.org/ontology/use-case#")
STORY = Namespace("https://ekgf.org/ontology/story#")
SH = Namespace("http://www.w3.org/ns/shacl#")
META = Namespace("https://ekgf.org/ontology/shape#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
EX = Namespace("https://example.test/")
RELATIONSHIP = URIRef("urn:uuid:fa48a552-6f45-4f01-872e-0146622295d6")
OTHER_RELATIONSHIP = URIRef("urn:uuid:4fabf150-e1e0-4414-91a7-11b31f92d3ad")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


class OutcomeRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outcome = Graph().parse(ROOT / "ekgf-outcome.ttl", format="turtle")
        cls.use_case = Graph().parse(ROOT / "ekgf-use-case.ttl", format="turtle")
        cls.ontology = cls.outcome + cls.use_case

    def fixture(self, forward=False):
        data = Graph()
        data.add((RELATIONSHIP, RDF.type, OUTCOME.OutcomeRelationship))
        data.add((EX.useCase, RDF.type, USE_CASE.UseCase))
        data.add((EX.outcome, RDF.type, OUTCOME.Outcome))
        data.add((EX.useCase, USE_CASE.outcomeLink, RELATIONSHIP) if forward else
                 (RELATIONSHIP, OUTCOME.useCase, EX.useCase))
        data.add((RELATIONSHIP, OUTCOME.targetOutcome, EX.outcome))
        return data

    def assert_valid(self, data, expected=True, inference="rdfs", **options):
        conforms, _, report = validate(
            data, shacl_graph=self.outcome, ont_graph=self.ontology,
            inference=inference, do_owl_imports=False, **options,
        )
        self.assertEqual(conforms, expected, report)

    def reason(self, data):
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def test_relationship_class_and_endpoint_cardinalities_are_declared(self):
        self.assertIn((OUTCOME.OutcomeRelationship, RDF.type, OWL.Class), self.outcome)
        restrictions = set(self.outcome.objects(OUTCOME.OutcomeRelationship,
                                               RDFS.subClassOf))
        for predicate in (OUTCOME.useCase, OUTCOME.targetOutcome):
            with self.subTest(predicate=predicate):
                self.assertTrue(any(
                    (node, OWL.onProperty, predicate) in self.outcome
                    and any(int(value) == 1 for value in
                            self.outcome.objects(node, OWL.cardinality))
                    for node in restrictions
                ))

    def test_either_direction_infers_inverse_types_and_summary(self):
        for forward in (False, True):
            with self.subTest(forward=forward):
                data = self.fixture(forward)
                data.remove((None, RDF.type, None))
                graph = self.reason(data)
                for triple in (
                    (RELATIONSHIP, RDF.type, OUTCOME.OutcomeRelationship),
                    (EX.useCase, RDF.type, USE_CASE.UseCase),
                    (EX.outcome, RDF.type, OUTCOME.Outcome),
                    (RELATIONSHIP, OUTCOME.useCase, EX.useCase),
                    (EX.useCase, USE_CASE.outcomeLink, RELATIONSHIP),
                    (EX.useCase, USE_CASE.hasOutcome, EX.outcome),
                ):
                    self.assertIn(triple, graph)
                self.assertFalse(list(graph.objects(None, ERROR)))
                self.assert_valid(data)

    def test_sources_are_counted_in_both_directions_without_inference(self):
        for forward in (False, True):
            with self.subTest(forward=forward):
                data = self.fixture(forward)
                self.assert_valid(data, inference="none")
                data.add((EX.useCase, USE_CASE.outcomeLink, RELATIONSHIP))
                data.add((RELATIONSHIP, OUTCOME.useCase, EX.useCase))
                self.assert_valid(data, inference="none")

    def test_missing_endpoints_fail_for_instances_subclasses_and_predicate_targets(self):
        for kind in (OUTCOME.OutcomeRelationship, EX.SpecialContribution):
            for missing in (OUTCOME.useCase, OUTCOME.targetOutcome):
                with self.subTest(kind=kind, missing=missing):
                    data = self.fixture()
                    data.set((RELATIONSHIP, RDF.type, kind))
                    data.add((EX.SpecialContribution, RDFS.subClassOf,
                              OUTCOME.OutcomeRelationship))
                    data.remove((RELATIONSHIP, missing, None))
                    self.assert_valid(data, False)
        for predicate, obj in (
            (OUTCOME.useCase, EX.useCase),
            (OUTCOME.targetOutcome, EX.outcome),
            (OUTCOME.contributionDescription, Literal("A contribution")),
        ):
            with self.subTest(predicate=predicate):
                data = Graph()
                data.add((RELATIONSHIP, predicate, obj))
                self.assert_valid(data, False, inference="none")
        data = Graph()
        data.add((EX.useCase, USE_CASE.outcomeLink, RELATIONSHIP))
        self.assert_valid(data, False, inference="none")

    def test_multiple_source_terms_fail_even_when_directions_are_mixed(self):
        for first_forward, second_forward in ((False, False), (True, True),
                                              (False, True)):
            with self.subTest(directions=(first_forward, second_forward)):
                data = self.fixture(first_forward)
                data.add((EX.otherUseCase, RDF.type, USE_CASE.UseCase))
                data.add((EX.otherUseCase, USE_CASE.outcomeLink, RELATIONSHIP)
                         if second_forward else
                         (RELATIONSHIP, OUTCOME.useCase, EX.otherUseCase))
                self.assert_valid(data, False, inference="none")

    def test_multiple_target_terms_fail_before_identity_reasoning(self):
        data = self.fixture()
        data.add((EX.otherOutcome, RDF.type, OUTCOME.Outcome))
        data.add((RELATIONSHIP, OUTCOME.targetOutcome, EX.otherOutcome))
        self.assert_valid(data, False, inference="none")

    def test_relationship_has_a_uuid_urn_identity(self):
        for node in (BNode(), Literal("relationship"), EX.relationship,
                     URIRef("urn:uuid:not-a-uuid")):
            with self.subTest(node=node):
                data = Graph()
                for subject, predicate, obj in self.fixture():
                    data.add((node if subject == RELATIONSHIP else subject,
                              predicate, obj))
                self.assert_valid(data, False)

    def test_endpoint_values_must_be_iris_of_the_expected_class(self):
        for predicate in (OUTCOME.useCase, OUTCOME.targetOutcome):
            for node in (BNode(), Literal("endpoint"), EX.untyped):
                with self.subTest(predicate=predicate, node=node):
                    data = self.fixture()
                    data.set((RELATIONSHIP, predicate, node))
                    self.assert_valid(data, False, inference="none")
        data = self.fixture(forward=True)
        data.remove((EX.useCase, USE_CASE.outcomeLink, RELATIONSHIP))
        data.add((Literal("use case"), USE_CASE.outcomeLink, RELATIONSHIP))
        self.assert_valid(data, False)

    def test_relationship_is_disjoint_from_source_and_target_roles(self):
        for kind in (OUTCOME.Outcome, USE_CASE.UseCase):
            with self.subTest(kind=kind):
                data = self.fixture()
                data.add((RELATIONSHIP, RDF.type, kind))
                self.assert_valid(data, False)
                self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_shared_endpoints_and_repeated_pairs_do_not_merge_relationships(self):
        for same_source, same_target in ((True, False), (False, True), (True, True)):
            with self.subTest(same_source=same_source, same_target=same_target):
                data = self.fixture()
                source = EX.useCase if same_source else EX.otherUseCase
                target = EX.outcome if same_target else EX.otherOutcome
                data.add((OTHER_RELATIONSHIP, RDF.type, OUTCOME.OutcomeRelationship))
                data.add((OTHER_RELATIONSHIP, OUTCOME.useCase, source))
                data.add((OTHER_RELATIONSHIP, OUTCOME.targetOutcome, target))
                data.add((source, RDF.type, USE_CASE.UseCase))
                data.add((target, RDF.type, OUTCOME.Outcome))
                data.add((RELATIONSHIP, OUTCOME.contributionDescription,
                          Literal("A first contribution", lang="en")))
                data.add((OTHER_RELATIONSHIP, OUTCOME.contributionDescription,
                          Literal("A separate contribution", lang="en")))
                data.add((RELATIONSHIP, OWL.differentFrom, OTHER_RELATIONSHIP))
                self.assert_valid(data)
                graph = self.reason(data)
                for first, second in ((RELATIONSHIP, OTHER_RELATIONSHIP),
                                      (EX.useCase, EX.otherUseCase),
                                      (EX.outcome, EX.otherOutcome)):
                    self.assertNotIn((first, OWL.sameAs, second), graph)
                self.assertFalse(list(graph.objects(None, ERROR)))

    def test_owl_reports_explicitly_distinct_conflicting_endpoints(self):
        for predicate, other in ((OUTCOME.useCase, EX.otherUseCase),
                                 (OUTCOME.targetOutcome, EX.otherOutcome)):
            with self.subTest(predicate=predicate):
                data = self.fixture()
                original = data.value(RELATIONSHIP, predicate)
                data.add((RELATIONSHIP, predicate, other))
                data.add((original, OWL.differentFrom, other))
                self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_description_is_optional_multilingual_and_nonblank_text(self):
        data = self.fixture()
        self.assert_valid(data)
        for description in (Literal("Cuts handling time", lang="en"),
                            Literal("Verkort de verwerkingstijd", lang="nl")):
            data.add((RELATIONSHIP, OUTCOME.contributionDescription, description))
        self.assert_valid(data)
        for invalid in (Literal(""), Literal(" \n\t"), Literal(7), EX.description):
            with self.subTest(invalid=invalid):
                data = self.fixture()
                data.add((RELATIONSHIP, OUTCOME.contributionDescription, invalid))
                self.assert_valid(data, False)

    def test_outcome_priority_stays_on_the_outcome(self):
        data = self.fixture()
        data.add((EX.outcome, OUTCOME.priority, Literal(1)))
        self.assert_valid(data)
        data.add((RELATIONSHIP, OUTCOME.priority, Literal(2)))
        self.assert_valid(data, False)
        self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_parentage_and_reuse_do_not_inherit_outcomes_or_assert_ownership(self):
        data = self.fixture()
        data.add((EX.child, USE_CASE.isPartOf, EX.useCase))
        data.add((EX.reused, USE_CASE.isUsedIn, EX.useCase))
        graph = self.reason(data)
        for node in (EX.child, EX.reused):
            self.assertEqual(list(graph.objects(node, USE_CASE.outcomeLink)), [])
            self.assertEqual(list(graph.objects(node, USE_CASE.hasOutcome)), [])
        for predicate in (USE_CASE.usedIn, USE_CASE.ownsOutcome,
                          OUTCOME.isOutcomeOwnedBy):
            self.assertEqual(list(graph.triples((None, predicate, None))), [])

    def test_direct_summaries_and_story_contributions_do_not_invent_relationships(self):
        data = Graph()
        data.add((EX.useCase, USE_CASE.hasOutcome, EX.outcome))
        data.add((EX.resource, OUTCOME.hasOutcome, EX.outcome))
        data.add((EX.story, STORY.contributesTo, EX.outcome))
        graph = self.reason(data)
        self.assertEqual(list(graph.subjects(RDF.type, OUTCOME.OutcomeRelationship)), [])
        self.assert_valid(data)

    def test_snapshot_context_counts_distinct_endpoint_terms(self):
        dataset = Dataset()
        merged = Graph()
        for name, source in ((EX.firstSnapshot, EX.firstVersion),
                             (EX.secondSnapshot, EX.secondVersion)):
            snapshot = dataset.graph(name)
            snapshot += self.fixture()
            snapshot.set((RELATIONSHIP, OUTCOME.useCase, source))
            snapshot.add((source, RDF.type, USE_CASE.UseCase))
            self.assert_valid(snapshot)
            merged += snapshot
        self.assert_valid(merged, False)

    def test_validators_are_registered_bound_and_pass_shacl_meta_validation(self):
        self.assertIn((OUTCOME.ValidationShapeSet, META.hasShape,
                       OUTCOME.OutcomeRelationshipShape), self.outcome)
        self.assertIn((OUTCOME.ValidationShapeSet, META.hasShapesGraph,
                       URIRef(str(OUTCOME))), self.outcome)
        self.assertIn((URIRef(str(OUTCOME)), RDF.type, SH.ShapesGraph), self.outcome)
        self.assert_valid(self.fixture(), meta_shacl=True)

    def test_new_terms_have_english_markdown_explanations(self):
        for term in (URIRef(str(OUTCOME)), OUTCOME.OutcomeRelationship,
                     OUTCOME.useCase, OUTCOME.targetOutcome,
                     OUTCOME.contributionDescription, OUTCOME.OutcomeRelationshipShape,
                     OUTCOME.ValidationShapeSet, USE_CASE.outcomeLink, USE_CASE.hasOutcome):
            with self.subTest(term=term):
                self.assertTrue(any(
                    isinstance(value, Literal) and value.language == "en"
                    and len(str(value)) > 100
                    for value in self.ontology.objects(term, ANNOTATION.markdownDescription)
                ))

    def test_documented_examples_validate_and_query_contributions(self):
        text = (ROOT / "docs/outcome-relationships.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data)
        query, = re.findall(r"```sparql\n(.*?)```", text, re.DOTALL)
        rows = list(data.query(query))
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.useCase for row in rows}, {EX.caseReview, EX.caseIntake})
        self.assertEqual({row.outcome for row in rows}, {EX.shorterHandlingTime})
        self.assertTrue(all(str(row.contribution).strip() for row in rows))
        graph = self.reason(data)
        for row in rows:
            self.assertIn((row.useCase, USE_CASE.hasOutcome, row.outcome), graph)


if __name__ == "__main__":
    unittest.main()
