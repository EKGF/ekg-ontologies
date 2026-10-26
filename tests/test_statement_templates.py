"""Template documents declare their language and render into executable SPARQL."""

from pathlib import Path
import re
from string import Template
import unittest

from owlrl import DeductiveClosure, OWLRL_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
CONCEPT = Namespace("https://ekgf.org/ontology/concept#")
STORY = Namespace("https://ekgf.org/ontology/story#")
SPARQL = Namespace("https://ekgf.org/ontology/story-impl-sparql#")
EX = Namespace("https://example.test/")


class StatementTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph()
        for name in ("concept", "story", "story-impl-sparql"):
            cls.ontology.parse(ROOT / f"ekgf-{name}.ttl", format="turtle")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def language(self, data, node=EX.language):
        data.add((node, RDF.type, CONCEPT.TemplateLanguage))
        data.add((node, RDFS.label, Literal("Python string.Template syntax", lang="en")))
        data.add((node, RDFS.seeAlso,
                  URIRef("https://docs.python.org/3/library/string.html#template-strings")))

    def fixture(self):
        data = Graph()
        data.add((EX.story, STORY.implementedBy, EX.implementation))
        data.add((EX.implementation, SPARQL.hasTemplate, EX.template))
        data.add((EX.implementation, SPARQL.usesRenderer, EX.renderer))
        data.add((EX.template, SPARQL.templateText,
                  Literal('SELECT ?s WHERE { ?s <https://example.test/id> ${m} }')))
        data.add((EX.template, CONCEPT.templateLanguage, EX.language))
        data.add((EX.renderer, SPARQL.supportsTemplateLanguage, EX.language))
        self.language(data)
        return data

    def test_template_links_infer_document_renderer_and_implementation_types(self):
        data = self.fixture()
        self.assert_valid(data)
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        for node, kind in ((EX.implementation, SPARQL.StorySPARQLTemplateImplementation),
                           (EX.implementation, STORY.StoryImplementation),
                           (EX.template, SPARQL.StatementTemplate),
                           (EX.renderer, SPARQL.TemplateRenderer)):
            with self.subTest(node=node, kind=kind):
                self.assertIn((node, RDF.type, kind), graph)

    def test_template_implementation_requires_one_template_and_one_renderer(self):
        for missing in (SPARQL.hasTemplate, SPARQL.usesRenderer):
            with self.subTest(missing=missing):
                data = self.fixture()
                data.add((EX.implementation, RDF.type, SPARQL.StorySPARQLTemplateImplementation))
                data.remove((EX.implementation, missing, None))
                self.assert_valid(data, False)
        for predicate, extra in ((SPARQL.hasTemplate, EX.otherTemplate),
                                 (SPARQL.usesRenderer, EX.otherRenderer)):
            with self.subTest(predicate=predicate):
                data = self.fixture()
                original = data.value(EX.implementation, predicate)
                for _, p, value in list(data.triples((original, None, None))):
                    data.add((extra, p, value))
                data.add((EX.implementation, predicate, extra))
                self.assert_valid(data, False)

    def test_document_requires_source_and_exactly_one_language(self):
        for missing in (SPARQL.templateText, CONCEPT.templateLanguage):
            with self.subTest(missing=missing):
                data = self.fixture()
                data.remove((EX.template, missing, None))
                self.assert_valid(data, False)
        data = self.fixture()
        self.language(data, EX.otherLanguage)
        data.add((EX.template, CONCEPT.templateLanguage, EX.otherLanguage))
        data.add((EX.renderer, SPARQL.supportsTemplateLanguage, EX.otherLanguage))
        self.assert_valid(data, False)

    def test_template_source_can_be_inline_or_in_a_file_or_both(self):
        for mode in ("inline", "file", "both"):
            with self.subTest(mode=mode):
                data = self.fixture()
                if mode != "inline":
                    data.add((EX.template, SPARQL.templateFileName, Literal("lookup.rq.template")))
                if mode == "file":
                    data.remove((EX.template, SPARQL.templateText, None))
                self.assert_valid(data)

    def test_renderer_must_explicitly_support_the_document_language(self):
        data = self.fixture()
        data.remove((EX.renderer, SPARQL.supportsTemplateLanguage, None))
        self.assert_valid(data, False)
        self.language(data, EX.otherLanguage)
        data.add((EX.renderer, SPARQL.supportsTemplateLanguage, EX.otherLanguage))
        self.assert_valid(data, False)

    def test_template_and_native_sparql_source_are_not_interchangeable(self):
        for predicate in (SPARQL.sparql, SPARQL.fileName):
            with self.subTest(predicate=predicate):
                data = self.fixture()
                data.add((EX.implementation, predicate, Literal("unexpanded source")))
                self.assert_valid(data, False)
        data = Graph()
        data.add((EX.story, STORY.implementedBy, EX.implementation))
        data.add((EX.implementation, SPARQL.sparql, Literal("ASK {}")))
        self.assert_valid(data)

    def test_placeholder_requires_one_documented_language_and_a_token(self):
        for missing in (None, CONCEPT.templateLanguage, CONCEPT.manifestationValue):
            with self.subTest(missing=missing):
                data = Graph()
                self.language(data)
                data.add((EX.placeholder, RDF.type, CONCEPT.TemplateParameterManifestation))
                data.add((EX.placeholder, CONCEPT.templateLanguage, EX.language))
                data.add((EX.placeholder, CONCEPT.manifestationValue, Literal("${m}")))
                if missing is not None:
                    data.remove((EX.placeholder, missing, None))
                self.assert_valid(data, missing is None)

    def test_retired_placeholder_class_is_rejected_even_with_canonical_metadata(self):
        for canonical_type in (False, True):
            for language in (False, True):
                with self.subTest(canonical_type=canonical_type, language=language):
                    data = Graph()
                    data.add((EX.placeholder, RDF.type, CONCEPT.LegraDollarManifestation))
                    data.add((EX.placeholder, CONCEPT.manifestationValue, Literal("$m")))
                    if canonical_type:
                        data.add((EX.placeholder, RDF.type, CONCEPT.TemplateParameterManifestation))
                    if language:
                        self.language(data)
                        data.add((EX.placeholder, CONCEPT.templateLanguage, EX.language))
                    self.assert_valid(data, False)

    def test_migrated_placeholder_keeps_its_identity_and_requires_a_language(self):
        data = Graph()
        data.add((EX.concept, CONCEPT.hasManifestation, EX.placeholder))
        data.add((EX.occurrence, CONCEPT.occurrenceOf, EX.placeholder))
        data.add((EX.placeholder, RDF.type, CONCEPT.LegraDollarManifestation))
        data.add((EX.placeholder, CONCEPT.manifestationValue, Literal("$m")))
        self.assert_valid(data, False)

        data.remove((EX.placeholder, RDF.type, CONCEPT.LegraDollarManifestation))
        data.add((EX.placeholder, RDF.type, CONCEPT.TemplateParameterManifestation))
        self.assert_valid(data, False)

        self.language(data)
        data.add((EX.placeholder, CONCEPT.templateLanguage, EX.language))
        self.assert_valid(data)
        self.assertIn((EX.concept, CONCEPT.hasManifestation, EX.placeholder), data)
        self.assertIn((EX.occurrence, CONCEPT.occurrenceOf, EX.placeholder), data)

    def test_template_language_does_not_type_a_document_as_a_placeholder(self):
        data = self.fixture()
        graph = self.ontology + data
        DeductiveClosure(OWLRL_Semantics).expand(graph)
        self.assertNotIn((EX.template, RDF.type, CONCEPT.TemplateParameterManifestation), graph)

    def test_template_metadata_passes_standard_shacl_meta_validation(self):
        conforms, _, report = validate(
            self.fixture(), shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="rdfs", meta_shacl=True, do_owl_imports=False,
        )
        self.assertTrue(conforms, report)

    def test_documented_template_metadata_validates_with_all_three_ontologies(self):
        text = (ROOT / "docs/story-concept-usages.md").read_text()
        example, = re.findall(r"```turtle\n(.*?)```", text, re.DOTALL)
        data = Graph().parse(data=example, format="turtle")
        self.assert_valid(data)
        self.assertEqual(len(set(data.objects(None, SPARQL.hasTemplate))), 2)
        self.assertEqual(len(set(data.objects(None, SPARQL.usesRenderer))), 1)

    def test_rendering_an_rdf_literal_preserves_its_value_and_query_structure(self):
        value = 'A" . } UNION { ?s ?p ?o } # $other'
        source = Template('SELECT ?s WHERE { ?s <https://example.test/id> ${m} }')
        rendered = source.substitute(m=Literal(value).n3())
        data = Graph()
        data.add((EX.expected, EX.id, Literal(value)))
        data.add((EX.unrelated, EX.id, Literal("different")))
        self.assertEqual(list(data.query(rendered)), [(EX.expected,)])
        with self.assertRaises(KeyError):
            source.substitute({})


if __name__ == "__main__":
    unittest.main()
