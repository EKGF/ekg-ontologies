"""Public, locally defined vocabulary terms must carry usable documentation."""

from pathlib import Path
import unittest
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parents[1]
SH = Namespace("http://www.w3.org/ns/shacl#")
DCT = Namespace("http://purl.org/dc/terms/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")


def english(values):
    return [value for value in values if isinstance(value, Literal)
            and value.language in (None, "en") and str(value).strip()]


def english_definitions(graph, subject):
    return [value for predicate in (RDFS.comment, DCT.description, SKOS.definition,
                                   ANNOTATION.markdownDescription)
            for value in english(graph.objects(subject, predicate))]


class DocumentationCoverageTests(unittest.TestCase):
    def test_markdown_only_definition_is_usable_documentation(self):
        graph = Graph()
        subject = URIRef("https://example.org/DocumentedTerm")
        description = Literal(
            "## Meaning\n\nA reusable meaning shared across stories.", lang="en")
        graph.add((subject, ANNOTATION.markdownDescription, description))
        self.assertEqual(english_definitions(graph, subject), [description])

    def test_every_owned_named_term_has_label_definition_and_ontology(self):
        failures = []
        count = 0
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path, format="turtle")
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            declarations = list(graph.objects(ontology, SH.declare))
            namespaces = [str(graph.value(node, SH.namespace)) for node in declarations]
            for subject in set(graph.subjects(RDF.type, None)):
                if (not isinstance(subject, URIRef) or subject == ontology
                        or not any(str(subject).startswith(namespace) for namespace in namespaces)):
                    continue
                count += 1
                missing = []
                if not english(graph.objects(subject, RDFS.label)):
                    missing.append("English label")
                if not english_definitions(graph, subject):
                    missing.append("English definition")
                if (subject, RDFS.isDefinedBy, ontology) not in graph:
                    missing.append("defining ontology")
                if missing:
                    failures.append(f"{path.name}: {subject}: {', '.join(missing)}")
        self.assertGreater(count, 500)
        self.assertEqual(failures, [], "\n" + "\n".join(failures))

    def test_ontology_headers_have_name_description_and_license(self):
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path, format="turtle")
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            with self.subTest(path=path.name):
                self.assertTrue(english(graph.objects(ontology, RDFS.label)))
                self.assertTrue(english_definitions(graph, ontology))
                self.assertEqual(list(graph.objects(ontology, DCT.license)),
                                 [URIRef("https://creativecommons.org/publicdomain/zero/1.0/")])

    def test_capability_class_labels_describe_classes_not_example_instances(self):
        graph = Graph().parse(ROOT / "ekgf-capability.ttl", format="turtle")
        capability = Namespace("https://ekgf.org/ontology/capability#")
        for subject, label in [(capability.Capability, "Capability"),
                               (capability.SubCapability, "Sub-capability"),
                               (capability.Data_Sharing_and_Marketplace, "Data sharing and marketplace"),
                               (capability.Designing_and_Managing_Data_Products, "Designing and managing data products")]:
            with self.subTest(subject=subject):
                self.assertIn(Literal(label, lang="en"), graph.objects(subject, RDFS.label))

    def test_maturity_documentation_names_the_actual_domain_members(self):
        graph = Graph().parse(ROOT / "ekgf-maturity-model.ttl", format="turtle")
        maturity = Namespace("https://ekgf.org/ontology/ekgf-maturity-model#")
        for property, expected in [(maturity.hasCapability, ["pillar", "capability area"]),
                                   (maturity.inModel, ["capability", "capability area", "level", "pillar"])]:
            description = " ".join(str(value).lower() for value in graph.objects(property, RDFS.comment))
            for phrase in expected:
                with self.subTest(property=property, phrase=phrase):
                    self.assertIn(phrase, description)

    def test_namespace_serialization_hints_match_the_owned_namespace(self):
        import re
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph(bind_namespaces="none").parse(path, format="turtle")
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            namespaces = {str(graph.value(node, SH.namespace)) for node in graph.objects(ontology, SH.declare)}
            with self.subTest(path=path.name):
                default = dict(graph.namespaces()).get("")
                if default is not None:
                    self.assertIn(str(default), namespaces)
                for base in re.findall(r"(?im)^\s*@base\s+<([^>]+)>", path.read_text()):
                    self.assertIn(base, namespaces | {str(ontology)})

    def test_standard_dublin_core_terms_prefix_is_correct(self):
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph(bind_namespaces="none").parse(path, format="turtle")
            namespace = dict(graph.namespaces()).get("dct")
            if namespace is not None:
                with self.subTest(path=path.name):
                    self.assertEqual(namespace, URIRef("http://purl.org/dc/terms/"))

    def test_ontology_titles_follow_the_family_naming_convention(self):
        minor_words = {"and", "by", "for", "of", "the", "to"}
        for path in sorted(ROOT.glob("ekgf-*.ttl")):
            graph = Graph().parse(path, format="turtle")
            ontology, = graph.subjects(RDF.type, OWL.Ontology)
            labels = [value for value in graph.objects(ontology, RDFS.label)
                      if isinstance(value, Literal) and (value.language is None
                          or value.language.lower().split("-")[0] == "en")]
            with self.subTest(path=path.name):
                self.assertEqual(len(labels), 1,
                                 "Publish one canonical English ontology title")
                title = labels[0]
                self.assertEqual(title.language, "en")
                self.assertFalse(str(title).startswith(("EKGF ", "EKG ", "The ")))
                self.assertTrue(str(title).endswith(" Ontology"))
                self.assertEqual(str(title), str(title).strip())
                self.assertTrue(all(word in minor_words or word[0].isupper()
                                    for word in str(title).split()))

    def test_capability_vocabulary_has_no_digital_twin_terminology(self):
        import re
        graph = Graph().parse(ROOT / "ekgf-capability.ttl", format="turtle")
        ontology, = graph.subjects(RDF.type, OWL.Ontology)
        self.assertEqual(list(graph.objects(ontology, RDFS.label)),
                         [Literal("Capability Ontology", lang="en")])
        for subject, predicate, value in graph:
            if isinstance(value, Literal):
                with self.subTest(subject=subject, predicate=predicate):
                    self.assertIsNone(re.search(r"digital[ -]twin", str(value), re.I))
