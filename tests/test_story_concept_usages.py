"""Story-owned concept usages preserve reusable meanings and input defaults."""

from itertools import combinations, product
from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL


ROOT = Path(__file__).resolve().parents[1]
STORY = Namespace("https://ekgf.org/ontology/story#")
CONCEPT = Namespace("https://ekgf.org/ontology/concept#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")
ROLES = (
    (STORY.hasInputConcept, STORY.StoryInput),
    (STORY.hasOutputConcept, STORY.StoryOutput),
    (STORY.hasDependentConcept, STORY.StoryDependent),
)
FLAGS = (STORY.isMandatory, STORY.isServerProvided)


class StoryConceptUsageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = Graph().parse(ROOT / "ekgf-story.ttl", format="turtle")
        cls.ontology = cls.story + Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")

    def reason(self, data):
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        return graph

    def assert_valid(self, data, expected=True, inference="rdfs", inplace=False):
        conforms, _, report = validate(
            data, shacl_graph=self.story, ont_graph=self.ontology,
            inference=inference, do_owl_imports=False, inplace=inplace,
        )
        self.assertEqual(conforms, expected, report)

    def fixture(self, predicate=STORY.hasInputConcept, kind=STORY.StoryInput,
                usage=EX.usage):
        data = Graph()
        data.add((EX.story, RDF.type, STORY.Story))
        data.add((EX.story, predicate, usage))
        data.add((usage, RDF.type, kind))
        data.add((usage, CONCEPT.hasConcept, EX.concept))
        data.add((EX.concept, RDF.type, CONCEPT.DataElementConcept))
        return data

    def test_specific_links_infer_usage_types_and_general_link(self):
        data = Graph()
        usages = []
        for predicate, kind in ROLES:
            usage = BNode()
            usages.append((usage, kind))
            data.add((EX.story, predicate, usage))
            data.add((usage, CONCEPT.hasConcept, EX.concept))
        graph = self.reason(data)
        self.assertIn((EX.story, RDF.type, STORY.Story), graph)
        self.assertIn((EX.concept, RDF.type, CONCEPT.DataElementConcept), graph)
        self.assertNotIn((EX.concept, RDF.type, STORY.StoryConceptUsage), graph)
        for usage, kind in usages:
            with self.subTest(kind=kind):
                self.assertIn((usage, RDF.type, kind), graph)
                self.assertIn((usage, RDF.type, STORY.StoryConceptUsage), graph)
                self.assertIn((EX.story, STORY.hasConceptUsage, usage), graph)
                self.assertNotIn((usage, RDF.type, CONCEPT.DataElementConcept), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_named_and_blank_usages_validate_for_each_role(self):
        for predicate, kind in ROLES:
            for usage in (EX.usage, BNode()):
                with self.subTest(kind=kind, usage=usage):
                    self.assert_valid(self.fixture(predicate, kind, usage))

    def test_general_link_requires_one_resolved_role(self):
        for _, kind in ROLES:
            with self.subTest(kind=kind):
                self.assert_valid(self.fixture(STORY.hasConceptUsage, kind))
        data = self.fixture(STORY.hasConceptUsage, STORY.StoryConceptUsage)
        self.assert_valid(data, False)

    def test_input_flags_infer_the_role_of_a_general_usage_link(self):
        for flag in FLAGS:
            with self.subTest(flag=flag):
                data = self.fixture(STORY.hasConceptUsage, STORY.StoryConceptUsage)
                data.add((EX.usage, flag, Literal(False)))
                self.assert_valid(data)
                graph = self.reason(data)
                self.assertIn((EX.usage, RDF.type, STORY.StoryInput), graph)
                self.assertFalse(list(graph.objects(None, ERROR)))

    def test_missing_owner_or_concept_is_rejected_including_subclasses(self):
        for predicate, kind in ROLES:
            for missing in ("owner", "concept"):
                with self.subTest(kind=kind, missing=missing):
                    data = self.fixture(predicate, kind)
                    data.remove((EX.usage, RDF.type, kind))
                    data.add((EX.SpecializedUsage, RDFS.subClassOf, kind))
                    data.add((EX.usage, RDF.type, EX.SpecializedUsage))
                    if missing == "owner":
                        data.remove((EX.story, predicate, EX.usage))
                    else:
                        data.remove((EX.usage, CONCEPT.hasConcept, EX.concept))
                    self.assert_valid(data, False)

    def test_multiple_owners_are_rejected_across_specialized_and_general_links(self):
        for second_predicate in (STORY.hasInputConcept, STORY.hasConceptUsage):
            with self.subTest(second_predicate=second_predicate):
                data = self.fixture()
                data.add((EX.otherStory, RDF.type, STORY.Story))
                data.add((EX.otherStory, second_predicate, EX.usage))
                self.assert_valid(data, False, inference="none")

    def test_repeated_links_from_one_owner_count_once(self):
        data = self.fixture()
        data.add((EX.story, STORY.hasConceptUsage, EX.usage))
        self.assert_valid(data)

    def test_multiple_concepts_are_rejected(self):
        data = self.fixture()
        data.add((EX.usage, CONCEPT.hasConcept, EX.otherConcept))
        data.add((EX.otherConcept, RDF.type, CONCEPT.DataElementConcept))
        self.assert_valid(data, False)

    def test_owl_rejects_explicitly_distinct_owners_or_concepts(self):
        for conflict in ("owners", "concepts"):
            with self.subTest(conflict=conflict):
                data = self.fixture()
                if conflict == "owners":
                    data.add((EX.otherStory, STORY.hasConceptUsage, EX.usage))
                    data.add((EX.story, OWL.differentFrom, EX.otherStory))
                else:
                    data.add((EX.usage, CONCEPT.hasConcept, EX.otherConcept))
                    data.add((EX.concept, OWL.differentFrom, EX.otherConcept))
                self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_shared_concept_does_not_merge_stories_or_their_usages(self):
        data = self.fixture()
        data.add((EX.otherStory, STORY.hasInputConcept, EX.otherUsage))
        data.add((EX.otherUsage, CONCEPT.hasConcept, EX.concept))
        data.add((EX.story, OWL.differentFrom, EX.otherStory))
        data.add((EX.usage, OWL.differentFrom, EX.otherUsage))
        self.assert_valid(data)
        graph = self.reason(data)
        self.assertNotIn((EX.story, OWL.sameAs, EX.otherStory), graph)
        self.assertNotIn((EX.usage, OWL.sameAs, EX.otherUsage), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_usages_of_one_concept_on_one_story_keep_distinct_flags(self):
        data = self.fixture()
        data.add((EX.story, STORY.hasInputConcept, EX.otherUsage))
        data.add((EX.otherUsage, CONCEPT.hasConcept, EX.concept))
        data.add((EX.usage, OWL.differentFrom, EX.otherUsage))
        for usage, mandatory, provided in ((EX.usage, True, False),
                                            (EX.otherUsage, False, True)):
            data.add((usage, STORY.isMandatory, Literal(mandatory)))
            data.add((usage, STORY.isServerProvided, Literal(provided)))
        self.assert_valid(data)
        graph = self.reason(data)
        self.assertNotIn((EX.usage, OWL.sameAs, EX.otherUsage), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))
        for usage, mandatory, provided in ((EX.usage, True, False),
                                            (EX.otherUsage, False, True)):
            with self.subTest(usage=usage):
                self.assertEqual(set(graph.objects(usage, STORY.isMandatory)),
                                 {Literal(mandatory)})
                self.assertEqual(set(graph.objects(usage, STORY.isServerProvided)),
                                 {Literal(provided)})

    def test_a_concept_cannot_double_as_its_usage(self):
        data = self.fixture(usage=EX.concept)
        self.assert_valid(data, False)
        self.assertTrue(list(self.reason(data).objects(None, ERROR)))

    def test_different_roles_use_separate_usage_objects(self):
        for (first_predicate, first_kind), (second_predicate, second_kind) in combinations(ROLES, 2):
            with self.subTest(first_kind=first_kind, second_kind=second_kind):
                data = self.fixture(first_predicate, first_kind)
                data.add((EX.story, second_predicate, EX.usage))
                self.assert_valid(data, False)
                self.assertTrue(list(self.reason(data).objects(None, ERROR)))
                data.remove((EX.story, second_predicate, EX.usage))
                data.add((EX.story, second_predicate, EX.otherUsage))
                data.add((EX.otherUsage, CONCEPT.hasConcept, EX.concept))
                self.assert_valid(data)

    def test_input_flags_accept_independent_boolean_values(self):
        for mandatory, provided in product((False, True), repeat=2):
            with self.subTest(mandatory=mandatory, provided=provided):
                data = self.fixture()
                data.add((EX.usage, STORY.isMandatory, Literal(mandatory)))
                data.add((EX.usage, STORY.isServerProvided, Literal(provided)))
                self.assert_valid(data)

    def test_absent_flags_validate_without_materializing_defaults(self):
        data = self.fixture()
        self.assert_valid(data, inplace=True)
        graph = self.reason(data)
        for flag in FLAGS:
            with self.subTest(flag=flag):
                self.assertFalse(list(data.objects(EX.usage, flag)))
                self.assertFalse(list(graph.objects(EX.usage, flag)))
                shapes = [shape for shape in self.story.objects(STORY.StoryInputShape, SH.property)
                          if (shape, SH.path, flag) in self.story]
                self.assertEqual(len(shapes), 1)
                self.assertEqual(set(self.story.objects(shapes[0], SH.defaultValue)),
                                 {Literal(False)})

    def test_invalid_or_conflicting_flags_are_rejected(self):
        for flag in FLAGS:
            for values in ((Literal("true"),), (Literal(1),), (EX.value,),
                           (Literal(True), Literal(False))):
                with self.subTest(flag=flag, values=values):
                    data = self.fixture()
                    for value in values:
                        data.add((EX.usage, flag, value))
                    self.assert_valid(data, False)

    def test_flags_are_only_for_input_usages(self):
        for predicate, kind in ROLES[1:]:
            for flag in FLAGS:
                with self.subTest(kind=kind, flag=flag):
                    data = self.fixture(predicate, kind)
                    data.add((EX.usage, flag, Literal(False)))
                    self.assert_valid(data, False)

    def test_input_flags_cannot_bypass_owner_and_concept_validation(self):
        for flag in FLAGS:
            with self.subTest(flag=flag):
                data = Graph()
                data.add((EX.usage, flag, Literal(True)))
                self.assert_valid(data, False)

    def test_literal_usage_and_concept_links_are_rejected(self):
        for predicate, kind in ROLES:
            for endpoint in ("usage", "concept"):
                with self.subTest(kind=kind, endpoint=endpoint):
                    data = self.fixture(predicate, kind)
                    if endpoint == "usage":
                        data.add((EX.story, predicate, Literal("usage")))
                    else:
                        data.remove((EX.usage, CONCEPT.hasConcept, EX.concept))
                        data.add((EX.usage, CONCEPT.hasConcept, Literal("concept")))
                    self.assert_valid(data, False)

    def test_retired_predicates_are_undeclared_and_rejected(self):
        for predicate, value in ((STORY.hasInput, EX.usage),
                                 (STORY.hasOutput, EX.usage),
                                 (STORY.serverProvidedIRI, Literal(True))):
            with self.subTest(predicate=predicate):
                self.assertFalse(list(self.story.objects(predicate, RDF.type)))
                data = self.fixture()
                data.add((EX.story, predicate, value))
                self.assert_valid(data, False)

    def test_retired_parameter_classes_are_undeclared_and_rejected(self):
        for kind in (STORY.MandatoryParameter, STORY.OptionalParameter,
                     STORY.OptionalStoryOutput):
            with self.subTest(kind=kind):
                self.assertNotIn((kind, RDF.type, OWL.Class), self.story)
                data = self.fixture()
                data.add((EX.usage, RDF.type, kind))
                self.assert_valid(data, False)

    def test_general_has_concept_does_not_impose_story_usage_or_local_cardinality(self):
        self.assertFalse(list(self.ontology.objects(CONCEPT.hasConcept, RDFS.domain)))
        data = Graph()
        data.add((EX.resource, CONCEPT.hasConcept, EX.firstConcept))
        data.add((EX.resource, CONCEPT.hasConcept, EX.secondConcept))
        data.add((EX.firstConcept, OWL.differentFrom, EX.secondConcept))
        self.assert_valid(data)
        graph = self.reason(data)
        self.assertNotIn((EX.resource, RDF.type, STORY.StoryConceptUsage), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_documented_example_validates_and_reuses_one_template_manifestation(self):
        document = (ROOT / "docs/story-concept-usages.md").read_text()
        examples = re.findall(r"```turtle\n(.*?)```", document, re.DOTALL)
        self.assertEqual(len(examples), 1)
        data = Graph().parse(data=examples[0], format="turtle")
        conforms, _, report = validate(
            data, shacl_graph=self.story, ont_graph=self.story,
            inference="rdfs", do_owl_imports=False,
        )
        self.assertTrue(conforms, report)
        manifestations = set(data.subjects(RDF.type, CONCEPT.TemplateParameterManifestation))
        self.assertEqual(len(manifestations), 1)
        manifestation, = manifestations
        self.assertEqual(set(data.objects(manifestation, RDFS.label)),
                         {Literal("$m")})
        self.assertEqual(set(data.objects(manifestation, CONCEPT.manifestationValue)),
                         {Literal("$m")})
        self.assertEqual(len(set(data.subjects(CONCEPT.occurrenceOf, manifestation))), 2)
        graph = self.reason(data)
        self.assertIn((manifestation, RDF.type, CONCEPT.TemplateParameterManifestation), graph)
        self.assertNotIn((manifestation, RDF.type, CONCEPT.SPARQLVariableManifestation), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))


if __name__ == "__main__":
    unittest.main()
