"""Sightings record where and how a concept manifests, and what that implies."""

from itertools import combinations
from pathlib import Path
import re
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
CONCEPT = Namespace("https://ekgf.org/ontology/concept#")
STORY = Namespace("https://ekgf.org/ontology/story#")
DATASET = Namespace("https://ekgf.org/ontology/dataset#")
SH = Namespace("http://www.w3.org/ns/shacl#")
META = Namespace("https://ekgf.org/ontology/shape#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")
POSITIONS = {
    CONCEPT.ParameterPosition: STORY.StoryInput,
    CONCEPT.ProjectionPosition: STORY.StoryOutput,
    CONCEPT.GraphTemplatePosition: STORY.StoryOutput,
    CONCEPT.GraphPatternPosition: STORY.StoryDependent,
}
ROLE_LINKS = {
    STORY.StoryInput: STORY.hasInputConcept,
    STORY.StoryOutput: STORY.hasOutputConcept,
    STORY.StoryDependent: STORY.hasDependentConcept,
}


class SightingSourceTests(unittest.TestCase):
    """Concept Ontology: where an occurrence was found and its statement position."""

    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")

    def assert_valid(self, data, expected=True, inference="rdfs"):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference=inference, do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def sighting(self, data=None, node=EX.sighting, artifacts=(EX.implementation,),
                 positions=()):
        data = Graph() if data is None else data
        data.add((node, RDF.type, CONCEPT.ManifestationOccurrence))
        data.add((node, CONCEPT.occurrenceOf, EX.variable))
        data.add((EX.variable, RDF.type, CONCEPT.SPARQLVariableManifestation))
        for artifact in artifacts:
            data.add((node, CONCEPT.foundIn, artifact))
        for position in positions:
            data.add((node, CONCEPT.statementPosition, position))
        return data

    def test_found_in_infers_the_occurrence_and_accepts_several_artifacts(self):
        data = Graph()
        for artifact in (EX.implementation, EX.template, EX.dataset):
            data.add((EX.sighting, CONCEPT.foundIn, artifact))
        data.add((EX.dataset, RDF.type, DATASET.Dataset))
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertIn((EX.sighting, RDF.type, CONCEPT.ManifestationOccurrence), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))
        self.assertNotIn((CONCEPT.foundIn, RDF.type, OWL.FunctionalProperty), self.ontology)
        self.assert_valid(data)

    def test_found_in_accepts_named_and_blank_artifacts(self):
        self.assert_valid(self.sighting(artifacts=(BNode(), EX.dataset)))

    def test_found_in_rejects_literal_artifacts(self):
        self.assert_valid(self.sighting(artifacts=(Literal("stories/count.rq"),)), False)
        self.assert_valid(self.sighting(artifacts=(Literal("stories/count.rq"),)), False,
                          inference="none")

    def test_found_in_rejects_occurrences_concepts_manifestations_and_positions(self):
        for kind in (CONCEPT.ManifestationOccurrence, CONCEPT.DataElementConcept,
                     CONCEPT.SPARQLVariableManifestation, CONCEPT.StatementPosition):
            with self.subTest(kind=kind):
                data = self.sighting(artifacts=(EX.artifact,))
                data.add((EX.artifact, RDF.type, kind))
                self.assert_valid(data, False)

    def test_found_in_cannot_be_asserted_on_a_concept_or_manifestation(self):
        for kind in (CONCEPT.DataElementConcept, CONCEPT.BusinessTerm):
            with self.subTest(kind=kind):
                data = Graph()
                data.add((EX.thing, RDF.type, kind))
                data.add((EX.thing, CONCEPT.foundIn, EX.dataset))
                self.assert_valid(data, False)

    def test_built_in_positions_are_distinct_documented_individuals(self):
        for position in POSITIONS:
            with self.subTest(position=position):
                self.assertIn((position, RDF.type, OWL.NamedIndividual), self.ontology)
                self.assertIn((position, RDF.type, CONCEPT.StatementPosition), self.ontology)
                self.assertTrue(list(self.ontology.objects(position, RDFS.label)))
                self.assertTrue(list(self.ontology.objects(position, RDFS.comment)))
                self.assertIn((position, RDFS.isDefinedBy, URIRef(str(CONCEPT))),
                              self.ontology)
        graph = Graph() + self.ontology
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        for left, right in combinations(POSITIONS, 2):
            with self.subTest(left=left, right=right):
                self.assertIn((left, OWL.differentFrom, right), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_positions_are_disjoint_from_concepts_manifestations_and_occurrences(self):
        for kind in (CONCEPT.DataElementConcept, CONCEPT.ConceptManifestation,
                     CONCEPT.ManifestationOccurrence):
            self.assertIn((CONCEPT.StatementPosition, OWL.disjointWith, kind), self.ontology)

    def test_each_built_in_position_validates_on_a_sighting(self):
        for position in POSITIONS:
            with self.subTest(position=position):
                self.assert_valid(self.sighting(positions=(position,)))

    def test_one_appearance_can_have_several_positions(self):
        data = self.sighting(positions=(CONCEPT.ParameterPosition,
                                        CONCEPT.GraphPatternPosition))
        self.assertNotIn((CONCEPT.statementPosition, RDF.type, OWL.FunctionalProperty),
                         self.ontology)
        self.assert_valid(data)

    def test_a_statement_position_requires_an_identified_artifact(self):
        self.assert_valid(self.sighting(artifacts=(), positions=(CONCEPT.ParameterPosition,)),
                          False)

    def test_sightings_without_artifacts_or_positions_remain_valid(self):
        self.assert_valid(self.sighting(artifacts=()))

    def test_positions_must_be_documented_iris(self):
        self.assert_valid(self.sighting(positions=(Literal("parameter"),)), False)
        self.assert_valid(self.sighting(positions=(EX.undocumented,)), False)
        data = self.sighting(positions=(EX.customPosition,))
        data.add((EX.customPosition, RDF.type, CONCEPT.StatementPosition))
        data.add((EX.customPosition, RDFS.label, Literal("Custom position", lang="en")))
        self.assert_valid(data, False)
        data.add((EX.customPosition, RDFS.comment,
                  Literal("An application-defined statement position.", lang="en")))
        self.assert_valid(data)

    def test_positions_without_inference_require_supplied_types(self):
        data = self.sighting(positions=(EX.customPosition,))
        data.add((EX.customPosition, RDFS.label, Literal("Custom position", lang="en")))
        data.add((EX.customPosition, RDFS.comment,
                  Literal("An application-defined statement position.", lang="en")))
        self.assert_valid(data, False, inference="none")
        data.add((EX.customPosition, RDF.type, CONCEPT.StatementPosition))
        self.assert_valid(data, inference="none")

    def test_a_concept_cannot_double_as_a_position(self):
        data = self.sighting(positions=(EX.concept,))
        data.add((EX.concept, RDF.type, CONCEPT.DataElementConcept))
        data.add((EX.concept, RDFS.label, Literal("Concept", lang="en")))
        data.add((EX.concept, RDFS.comment, Literal("A meaning.", lang="en")))
        self.assert_valid(data, False)

    def test_new_terms_and_validators_are_documented_and_registered(self):
        for term in (CONCEPT.foundIn, CONCEPT.statementPosition, CONCEPT.StatementPosition,
                     CONCEPT.OccurrenceSightingShape, CONCEPT.StatementPositionShape):
            with self.subTest(term=term):
                self.assertTrue(list(self.ontology.objects(term, ANNOTATION.markdownDescription)))
        shapes = set(self.ontology.objects(CONCEPT.ValidationShapeSet, META.hasShape))
        self.assertLessEqual({CONCEPT.OccurrenceSightingShape, CONCEPT.StatementPositionShape},
                             shapes)

    def test_data_element_concept_definition_covers_meaning_manifestations_and_sightings(self):
        definition, = self.ontology.objects(CONCEPT.DataElementConcept, RDFS.comment)
        text = str(definition)
        summary = ("A logical data element with all its various forms of physical "
                   "manifestations and their sightings.")
        self.assertTrue(text.startswith(summary), text)
        for phrase in ("business terms", "technical terms", "ManifestationOccurrence",
                       "compound data constructs"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        guide = (ROOT / "docs/concepts.md").read_text()
        quoted = " ".join(line.removeprefix("> ").strip()
                          for line in guide.splitlines() if line.startswith("> "))
        self.assertEqual(quoted, summary)


class UndeclaredConceptUsageTests(unittest.TestCase):
    """Story Ontology: position evidence compared with declared concept usages."""

    @classmethod
    def setUpClass(cls):
        cls.story = Graph().parse(ROOT / "ekgf-story.ttl", format="turtle")
        cls.ontology = cls.story + Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")

    def results(self, data, inference="rdfs", ontology=None):
        conforms, report, text = validate(
            data, shacl_graph=self.story,
            ont_graph=self.ontology if ontology is None else ontology,
            inference=inference, do_owl_imports=False,
        )
        rows = []
        for result in report.subjects(RDF.type, SH.ValidationResult):
            rows.append((report.value(result, SH.focusNode),
                         report.value(result, SH.value),
                         report.value(result, SH.resultSeverity),
                         str(report.value(result, SH.resultMessage))))
        return conforms, rows, text

    def warnings(self, data, **options):
        conforms, rows, text = self.results(data, **options)
        violations = [row for row in rows if row[2] != SH.Warning]
        self.assertEqual(violations, [], text)
        return sorted((focus, value, message) for focus, value, _, message in rows)

    def implemented_story(self, data=None, story=EX.story, implementation=EX.implementation,
              declared=(), owner_link=STORY.implementedBy):
        data = Graph() if data is None else data
        data.add((story, RDF.type, STORY.Story))
        if owner_link == STORY.implementedBy:
            data.add((story, STORY.implementedBy, implementation))
        else:
            data.add((implementation, STORY.implementationOf, story))
        for concept, role in declared:
            usage = BNode()
            data.add((story, ROLE_LINKS[role], usage))
            data.add((usage, RDF.type, role))
            data.add((usage, CONCEPT.hasConcept, concept))
            data.add((concept, RDF.type, CONCEPT.DataElementConcept))
        return data

    def sight(self, data, concept, positions, implementation=EX.implementation,
              node=None, inverse=False):
        node = BNode() if node is None else node
        manifestation = URIRef(f"{concept}-variable")
        data.add((concept, RDF.type, CONCEPT.DataElementConcept))
        if inverse:
            data.add((manifestation, CONCEPT.concept, concept))
        else:
            data.add((concept, CONCEPT.hasManifestation, manifestation))
        data.add((manifestation, RDF.type, CONCEPT.SPARQLVariableManifestation))
        data.add((node, CONCEPT.occurrenceOf, manifestation))
        data.add((node, CONCEPT.foundIn, implementation))
        for position in positions:
            data.add((node, CONCEPT.statementPosition, position))
        return node

    def test_built_in_positions_map_to_one_expected_usage_role(self):
        for position, role in POSITIONS.items():
            with self.subTest(position=position):
                self.assertEqual(set(self.story.objects(position, STORY.expectedUsageRole)),
                                 {role})
                self.assertIn((position, RDF.type, OWL.NamedIndividual), self.story)
                self.assertNotIn((position, RDFS.isDefinedBy, URIRef(str(STORY))), self.story)
        self.assertIn((STORY.expectedUsageRole, RDF.type, OWL.AnnotationProperty), self.story)

    def test_the_story_ontology_alone_supplies_the_position_mappings(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.assertEqual(len(self.warnings(data, ontology=self.story)), 1)

    def test_parameter_evidence_without_an_input_usage_warns(self):
        data = self.implemented_story(declared=((EX.category, STORY.StoryDependent),))
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        warnings = self.warnings(data)
        self.assertEqual(len(warnings), 1, warnings)
        focus, value, message = warnings[0]
        self.assertEqual((focus, value), (EX.implementation, EX.category))
        self.assertIn("Used, not declared", message)
        self.assertIn(str(STORY.StoryInput), message)

    def test_projection_and_graph_template_evidence_expect_output_usages(self):
        for position in (CONCEPT.ProjectionPosition, CONCEPT.GraphTemplatePosition):
            with self.subTest(position=position):
                data = self.implemented_story(declared=((EX.product, STORY.StoryInput),))
                self.sight(data, EX.product, (position,))
                warnings = self.warnings(data)
                self.assertEqual([(focus, value) for focus, value, _ in warnings],
                                 [(EX.implementation, EX.product)])
                self.assertIn(str(STORY.StoryOutput), warnings[0][2])

    def test_matching_declarations_satisfy_the_evidence(self):
        for position, role in POSITIONS.items():
            with self.subTest(position=position):
                data = self.implemented_story(declared=((EX.concept, role),))
                self.sight(data, EX.concept, (position,))
                self.assertEqual(self.warnings(data), [])

    def test_general_usage_link_with_explicit_role_satisfies_the_evidence(self):
        data = self.implemented_story()
        data.add((EX.story, STORY.hasConceptUsage, EX.usage))
        data.add((EX.usage, RDF.type, STORY.StoryInput))
        data.add((EX.usage, CONCEPT.hasConcept, EX.category))
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.assertEqual(self.warnings(data), [])
        self.assertEqual(self.warnings(data, inference="none"), [])

    def test_specialized_link_satisfies_the_evidence_without_inference(self):
        data = self.implemented_story(declared=((EX.category, STORY.StoryInput),))
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.assertEqual(self.warnings(data, inference="none"), [])

    def test_pattern_only_evidence_expects_some_declared_usage(self):
        data = self.implemented_story()
        self.sight(data, EX.status, (CONCEPT.GraphPatternPosition,))
        warnings = self.warnings(data)
        self.assertEqual([(focus, value) for focus, value, _ in warnings],
                         [(EX.implementation, EX.status)])
        self.assertIn(str(STORY.StoryDependent), warnings[0][2])
        for role in POSITIONS.values():
            with self.subTest(role=role):
                data = self.implemented_story(declared=((EX.status, role),))
                self.sight(data, EX.status, (CONCEPT.GraphPatternPosition,))
                self.assertEqual(self.warnings(data), [])

    def test_input_or_output_evidence_replaces_the_dependent_expectation(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,
                                       CONCEPT.GraphPatternPosition))
        self.sight(data, EX.category, (CONCEPT.GraphPatternPosition,))
        warnings = self.warnings(data)
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn(str(STORY.StoryInput), warnings[0][2])
        data = self.implemented_story(declared=((EX.category, STORY.StoryInput),))
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.sight(data, EX.category, (CONCEPT.GraphPatternPosition,))
        self.assertEqual(self.warnings(data), [])

    def test_one_concept_can_be_expected_as_input_and_output(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,
                                       CONCEPT.ProjectionPosition))
        messages = [message for _, _, message in self.warnings(data)]
        self.assertEqual(len(messages), 2, messages)
        self.assertTrue(any(str(STORY.StoryInput) in message for message in messages))
        self.assertTrue(any(str(STORY.StoryOutput) in message for message in messages))

    def test_repeated_sightings_report_each_missing_role_once(self):
        data = self.implemented_story()
        for _ in range(3):
            self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.assertEqual(len(self.warnings(data)), 1)

    def test_evidence_is_scoped_to_each_implementation_and_its_story(self):
        data = self.implemented_story(declared=((EX.category, STORY.StoryInput),))
        self.implemented_story(data, story=EX.otherStory, implementation=EX.otherImplementation)
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        self.sight(data, EX.category, (CONCEPT.GraphPatternPosition,),
                   implementation=EX.otherImplementation)
        warnings = self.warnings(data)
        self.assertEqual([(focus, value) for focus, value, _ in warnings],
                         [(EX.otherImplementation, EX.category)])
        self.assertIn(str(STORY.StoryDependent), warnings[0][2])

    def test_sightings_outside_story_implementations_are_not_compared(self):
        data = self.implemented_story()
        dataset_sighting = self.sight(data, EX.category, (CONCEPT.ParameterPosition,),
                                      implementation=EX.dataset)
        data.add((EX.dataset, RDF.type, DATASET.Dataset))
        self.assertEqual(self.warnings(data), [])
        data.add((dataset_sighting, CONCEPT.foundIn, EX.implementation))
        self.assertEqual(len(self.warnings(data)), 1)

    def test_ownership_and_manifestation_links_count_in_either_direction(self):
        data = self.implemented_story(owner_link=STORY.implementationOf)
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,), inverse=True)
        self.assertEqual([(focus, value) for focus, value, _ in self.warnings(data)],
                         [(EX.implementation, EX.category)])

    def test_preferred_manifestation_links_count_with_rdfs_inference(self):
        data = self.implemented_story()
        data.add((EX.category, CONCEPT.preferredResultColumnManifestation, EX.column))
        data.add((EX.sighting, CONCEPT.occurrenceOf, EX.column))
        data.add((EX.sighting, CONCEPT.foundIn, EX.implementation))
        data.add((EX.sighting, CONCEPT.statementPosition, CONCEPT.ProjectionPosition))
        self.assertEqual(len(self.warnings(data)), 1)

    def test_positions_without_an_expected_role_are_rejected(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (EX.customPosition,))
        conforms, rows, text = self.results(data)
        self.assertFalse(conforms)
        self.assertTrue(any(severity == SH.Violation and focus == EX.customPosition
                            for focus, _, severity, _ in rows), text)
        data.add((EX.customPosition, STORY.expectedUsageRole, STORY.StoryDependent))
        self.assertEqual(len(self.warnings(data)), 1)

    def test_expected_roles_must_be_one_story_usage_role(self):
        for roles in ((STORY.Story,), (STORY.StoryInput, STORY.StoryOutput),
                      (Literal("input"),)):
            with self.subTest(roles=roles):
                data = self.implemented_story()
                self.sight(data, EX.category, (EX.customPosition,))
                for role in roles:
                    data.add((EX.customPosition, STORY.expectedUsageRole, role))
                conforms, rows, text = self.results(data)
                self.assertTrue(any(severity == SH.Violation for _, _, severity, _ in rows),
                                text)

    def test_missing_mappings_fail_instead_of_skipping_the_comparison(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        conforms, rows, text = self.results(data, ontology=Graph())
        self.assertFalse(conforms)
        self.assertTrue(any(severity == SH.Violation and focus == CONCEPT.ParameterPosition
                            for focus, _, severity, _ in rows), text)

    def test_evidence_does_not_create_story_declarations(self):
        data = self.implemented_story()
        self.sight(data, EX.category, (CONCEPT.ParameterPosition,))
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertFalse(list(graph.subjects(RDF.type, STORY.StoryConceptUsage)))
        self.assertFalse(list(graph.objects(EX.story, STORY.hasInputConcept)))
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_new_story_terms_are_documented_and_registered(self):
        for term in (STORY.expectedUsageRole, STORY.UndeclaredConceptUsageShape,
                     STORY.StatementPositionUsageRoleShape):
            with self.subTest(term=term):
                self.assertTrue(list(self.story.objects(term, ANNOTATION.markdownDescription)))
        self.assertEqual(set(self.story.objects(STORY.UndeclaredConceptUsageShape,
                                                SH.severity)), {SH.Warning})
        shapes = set(self.story.objects(STORY.ValidationShapeSet, META.hasShape))
        self.assertLessEqual({STORY.UndeclaredConceptUsageShape,
                              STORY.StatementPositionUsageRoleShape}, shapes)


class DocumentedSightingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / "docs/manifestation-sightings.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        cls.query, = re.findall(r"```sparql\n(.*?)```", text, re.DOTALL)
        cls.data = Graph().parse(data=example, format="turtle")
        cls.concept = Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")
        cls.story = Graph().parse(ROOT / "ekgf-story.ttl", format="turtle")

    def test_documented_sightings_validate_against_the_concept_shapes(self):
        conforms, _, report = validate(
            self.data, shacl_graph=self.concept, ont_graph=self.concept,
            inference="rdfs", do_owl_imports=False,
        )
        self.assertTrue(conforms, report)

    def test_documented_story_comparison_reports_one_undeclared_input(self):
        conforms, report, text = validate(
            self.data, shacl_graph=self.story, ont_graph=self.story,
            inference="rdfs", do_owl_imports=False,
        )
        results = list(report.subjects(RDF.type, SH.ValidationResult))
        self.assertEqual(len(results), 1, text)
        result, = results
        self.assertEqual(report.value(result, SH.resultSeverity), SH.Warning)
        self.assertEqual(report.value(result, SH.focusNode), EX.listProductsImplementation)
        self.assertEqual(report.value(result, SH.value), EX.productCategory)
        self.assertIn(str(STORY.StoryInput), str(report.value(result, SH.resultMessage)))
        conforms, _, _ = validate(
            self.data, shacl_graph=self.story, ont_graph=self.story,
            inference="rdfs", do_owl_imports=False, allow_warnings=True,
        )
        self.assertTrue(conforms)

    def test_documented_query_lists_datasets_and_how_the_concept_appears(self):
        rows = {(row.dataset, row.how, row.position) for row in self.data.query(self.query)}
        self.assertEqual(rows, {
            (EX.catalogExtract, CONCEPT.RawSourceFieldManifestation, None),
            (EX.storyDefinitions, CONCEPT.TemplateParameterManifestation,
             CONCEPT.ParameterPosition),
            (EX.storyDefinitions, CONCEPT.TemplateParameterManifestation,
             CONCEPT.GraphPatternPosition),
        })


if __name__ == "__main__":
    unittest.main()
