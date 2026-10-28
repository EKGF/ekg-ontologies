"""Story purpose is an extensible classification, independent of execution."""

from itertools import combinations
from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
STORY = Namespace("https://ekgf.org/ontology/story#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
SPARQL = Namespace("https://ekgf.org/ontology/story-impl-sparql#")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")
BUILTINS = (
    STORY.StoryStereoTypeQuery,
    STORY.StoryStereoTypeUpdate,
    STORY.StoryStereoTypeTransformationRule,
    STORY.StoryStereoTypeValidationRule,
)


class StoryStereotypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-story.ttl", format="turtle")

    def assert_valid(self, data, expected=True, **options):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False, **options,
        )
        self.assertEqual(conforms, expected, report)

    def custom_stereotype(self, data, node=EX.customType, markdown=False):
        data.add((node, RDF.type, STORY.StoryStereoType))
        data.add((node, RDFS.label, Literal("Reconciliation", lang="en")))
        predicate = ANNOTATION.markdownDescription if markdown else RDFS.comment
        data.add((node, predicate,
                  Literal("Identifies and explains differences between source records.", lang="en")))

    def test_assignment_infers_story_and_stereotype_types(self):
        data = Graph()
        data.add((EX.story, STORY.hasStereoType, EX.customType))
        self.custom_stereotype(data)
        data.remove((EX.customType, RDF.type, STORY.StoryStereoType))
        self.assert_valid(data)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertIn((EX.story, RDF.type, STORY.Story), graph)
        self.assertIn((EX.customType, RDF.type, STORY.StoryStereoType), graph)

    def test_each_builtin_is_a_valid_named_classification(self):
        for stereotype in BUILTINS:
            with self.subTest(stereotype=stereotype):
                self.assertIn((stereotype, RDF.type, OWL.NamedIndividual), self.ontology)
                self.assertIn((stereotype, RDF.type, STORY.StoryStereoType), self.ontology)
                data = Graph()
                data.add((EX.story, STORY.hasStereoType, stereotype))
                self.assert_valid(data)

    def test_missing_classification_is_valid_and_has_no_default(self):
        data = Graph()
        data.add((EX.story, RDF.type, STORY.Story))
        self.assert_valid(data, inplace=True)
        self.assertEqual(list(data.objects(EX.story, STORY.hasStereoType)), [])
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(list(graph.objects(EX.story, STORY.hasStereoType)), [])

    def test_repeated_single_assignment_is_valid_but_multiple_terms_are_rejected(self):
        data = Graph()
        data.add((EX.story, STORY.hasStereoType, BUILTINS[0]))
        data.add((EX.story, STORY.hasStereoType, BUILTINS[0]))
        self.assert_valid(data)
        data.add((EX.story, STORY.hasStereoType, BUILTINS[1]))
        self.assert_valid(data, False)

    def test_custom_stereotypes_are_supported_with_a_label_and_definition(self):
        for markdown in (False, True):
            with self.subTest(markdown=markdown):
                data = Graph()
                self.custom_stereotype(data, markdown=markdown)
                data.add((EX.story, STORY.hasStereoType, EX.customType))
                self.assert_valid(data)

    def test_bare_or_undocumented_stereotype_iris_are_rejected(self):
        for missing in (None, RDFS.label, RDFS.comment):
            with self.subTest(missing=missing):
                data = Graph()
                data.add((EX.story, STORY.hasStereoType, EX.customType))
                if missing is not None:
                    self.custom_stereotype(data)
                    data.remove((EX.customType, missing, None))
                self.assert_valid(data, False)

    def test_stereotype_identity_is_an_iri_and_metadata_is_nonempty_text(self):
        for node in (BNode(), Literal("Query")):
            with self.subTest(node=node):
                data = Graph()
                self.custom_stereotype(data, node)
                data.add((EX.story, STORY.hasStereoType, node))
                self.assert_valid(data, False)
        for predicate in (RDFS.label, RDFS.comment):
            for value in (Literal(""), EX.notText):
                with self.subTest(predicate=predicate, value=value):
                    data = Graph()
                    self.custom_stereotype(data)
                    data.set((EX.customType, predicate, value))
                    data.add((EX.story, STORY.hasStereoType, EX.customType))
                    self.assert_valid(data, False)

    def test_custom_stereotype_subclasses_cannot_bypass_metadata_validation(self):
        data = Graph()
        data.add((EX.specialKind, RDFS.subClassOf, STORY.StoryStereoType))
        data.add((EX.customType, RDF.type, EX.specialKind))
        self.assert_valid(data, False)

    def test_one_stereotype_can_classify_many_distinct_stories(self):
        data = Graph()
        for story in (EX.firstStory, EX.secondStory):
            data.add((story, STORY.hasStereoType, BUILTINS[0]))
        data.add((EX.firstStory, OWL.differentFrom, EX.secondStory))
        self.assert_valid(data)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((EX.firstStory, OWL.sameAs, EX.secondStory), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_two_builtin_classifications_are_inconsistent_in_owl(self):
        for first, second in combinations(BUILTINS, 2):
            with self.subTest(first=first, second=second):
                graph = self.ontology + Graph()
                graph.add((EX.story, STORY.hasStereoType, first))
                graph.add((EX.story, STORY.hasStereoType, second))
                DeductiveClosure(OWLRL_Semantics).expand(graph)
                self.assertTrue(list(graph.objects(None, ERROR)))

    def test_story_and_implementation_roles_are_disjoint(self):
        data = Graph()
        data.add((EX.sameResource, RDF.type, STORY.Story))
        data.add((EX.sameResource, RDF.type, STORY.StoryImplementation))
        data.add((EX.sameResource, STORY.implementationOf, EX.owner))
        self.assert_valid(data, False)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertTrue(list(graph.objects(None, ERROR)))

    def test_implementation_and_usage_cannot_receive_story_classification(self):
        data = Graph()
        data.add((EX.story, STORY.implementedBy, EX.implementation))
        data.add((EX.implementation, STORY.hasStereoType, BUILTINS[0]))
        self.assert_valid(data, False)
        data = Graph()
        data.add((EX.story, STORY.hasInputConcept, EX.usage))
        data.add((EX.usage, Namespace("https://ekgf.org/ontology/concept#").hasConcept, EX.concept))
        data.add((EX.concept, RDF.type, Namespace("https://ekgf.org/ontology/concept#").DataElementConcept))
        data.add((EX.usage, STORY.hasStereoType, BUILTINS[0]))
        self.assert_valid(data, False)

    def test_classification_is_independent_of_implementation_language_and_flags(self):
        schema = self.ontology + Graph().parse(ROOT / "ekgf-story-impl-sparql.ttl", format="turtle")
        data = Graph()
        data.add((EX.story, STORY.implementedBy, EX.implementation))
        data.add((EX.implementation, RDF.type, SPARQL.CONSTRUCT))
        data.add((EX.story, STORY.isUpdate, Literal(True)))
        data.add((EX.story, STORY.isDeletion, Literal(False)))
        graph = schema + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(list(graph.objects(EX.story, STORY.hasStereoType)), [])
        data.add((EX.story, STORY.hasStereoType, BUILTINS[2]))
        self.assert_valid(data)
        graph = schema + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertEqual(set(graph.objects(EX.story, STORY.hasStereoType)), {BUILTINS[2]})
        self.assertNotIn((EX.story, RDF.type, SPARQL.StorySPARQLImplementation), graph)
        self.assertNotIn((EX.implementation, STORY.hasStereoType, BUILTINS[2]), graph)

    def test_classification_does_not_infer_mutation_flags(self):
        for stereotype in BUILTINS:
            with self.subTest(stereotype=stereotype):
                data = Graph()
                data.add((EX.story, STORY.hasStereoType, stereotype))
                graph = self.ontology + data
                DeductiveClosure(OWLRL_Semantics).expand(graph)
                for flag in (STORY.isUpdate, STORY.isDeletion):
                    self.assertEqual(list(graph.objects(EX.story, flag)), [])

    def test_shapes_pass_standard_shacl_meta_validation(self):
        data = Graph()
        data.add((EX.story, STORY.hasStereoType, BUILTINS[0]))
        self.assert_valid(data, meta_shacl=True)

    def test_documented_classifications_validate(self):
        text = (ROOT / "docs/story-stereotypes.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data)
        self.assertEqual(len(set(data.subjects(STORY.hasStereoType, None))), 5)


if __name__ == "__main__":
    unittest.main()
