"""Publication settings reuse the canonical registry without redefining it."""
import pathlib
import re
import unittest

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, RDFS

ROOT = pathlib.Path(__file__).resolve().parents[1]
GA = Namespace("https://ekgf.org/ontology/grapharch#")
ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
ARTPUB = Namespace("https://ekgf.org/ontology/artifact-publication#")
DOC = Namespace("urn:ekgf-ontologies:documentation:")
FAMILY = URIRef("urn:uuid:c0eda36a-f42a-4fa3-aea9-c7a5543207eb")
AUTHORITY = URIRef("urn:uuid:6c1408aa-039c-42f9-8dee-9c3f0009d61a")


class GraphArchPublicationTests(unittest.TestCase):
    def test_publication_links_use_the_site_navigation_bar(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        self.assertFalse(list(settings.objects(DOC.websiteProfile, GA.headerLink)))
        self.assertEqual(list(settings.objects(DOC.websiteProfile, GA.navigation)),
                         [DOC.siteNavigation])
        self.assertIn((DOC.siteNavigation, GA.navigationRegion, Literal("primary")), settings)
        self.assertEqual(set(settings.objects(DOC.siteNavigation, GA.navigationEntry)),
                         {DOC.familyLink, DOC.pdfLink})
        for entry, label, order, url in (
            (DOC.familyLink, "Ontology family", 1, "spec/main/"),
            (DOC.pdfLink, "PDF", 2, "urn:ekgf-ontologies:documentation:pdf"),
        ):
            self.assertIn((entry, RDF.type, GA.NavigationEntry), settings)
            self.assertEqual(str(settings.value(entry, DCTERMS.title)), label)
            self.assertEqual(int(settings.value(entry, GA.order)), order)
            self.assertEqual(str(settings.value(entry, GA.url)), url)

    def test_website_contains_the_reference_and_pdf_at_their_public_paths(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        self.assertEqual(str(settings.value(DOC.website, GA.destination)), "site")
        self.assertEqual(set(settings.objects(DOC.website, GA.containsTarget)),
                         {DOC.specification, DOC.pdf})
        self.assertEqual(str(settings.value(DOC.project, GA.contentSource)), "publication/site")
        for target, public, entry in ((DOC.specification, "spec/main", ""),
                                      (DOC.pdf, "pdf", "ekgf-spec-ekg-ontologies.pdf")):
            self.assertEqual(str(settings.value(target, GA.destination)), f"site/{public}")
            url = URIRef(f"https://ekgf.github.io/ekg-ontologies/{public}/{entry}")
            for field in (GA.thisVersion, GA.latestVersion):
                self.assertIn((target, field, url), settings)
        for target in (DOC.website, DOC.specification):
            self.assertEqual(str(settings.value(target, GA.documentationGraphPath)),
                             "documentation.nq")
        # The PDF target owns only its named PDF in pdf/.
        self.assertIsNone(settings.value(DOC.pdf, GA.documentationGraphPath))
        self.assertIn((DOC.pdf, GA.documentType, GA.SpecificationDocument), settings)
        self.assertIn((AUTHORITY, GA.slug, Literal("ekgf")), settings)
        self.assertIn((FAMILY, GA.slug, Literal("ekg-ontologies")), settings)
        hosting = (ROOT / "publication/hosting.yaml").read_text()
        self.assertEqual(hosting, "version: 2\nplatform: github-pages\nmount: /\n"
                                  "site: ../_site/site\n")

    def test_family_browser_and_ekgf_website_have_distinct_targets(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        self.assertEqual(set(settings.objects(DOC.project, GA.target)),
                         {DOC.website, DOC.specification, DOC.pdf})
        for target, renderer in ((DOC.specification, GA.SpecificationPagesRenderer),
                                 (DOC.pdf, GA.TypstRenderer),
                                 (DOC.website, GA.WebsiteRenderer)):
            self.assertEqual(list(settings.objects(target, GA.renderer)), [renderer])
        self.assertIn((DOC.website, GA.profile, DOC.websiteProfile), settings)
        self.assertFalse(list(settings.objects(None, GA.style)))
        self.assertEqual(list(settings.objects(DOC.websiteProfile, GA.theme)), [GA.EkgfTheme])
        self.assertEqual(list(settings.objects(DOC.pdfProfile, GA.theme)), [GA.SpecificationTheme])
        self.assertEqual({str(v) for v in settings.objects(DOC.profile, GA.requiredMetadataField)},
                         {"thisVersion", "latestVersion"})
        self.assertIn((DOC.websiteProfile, GA.layout, Literal("documentation")), settings)
        self.assertIn((FAMILY, GA.collectionTerm, Literal("family")), settings)
        self.assertIn((DOC.specification, GA.profile, DOC.profile), settings)
        self.assertIn((DOC.pdf, GA.profile, DOC.pdfProfile), settings)
        for profile in (DOC.profile, DOC.pdfProfile):
            self.assertIn((profile, ARTPUB.publishesFamily, FAMILY), settings)
        for subject in (DOC.specification, DOC.pdf):
            self.assertIn((subject, GA.publisher, AUTHORITY), settings)
        destinations = list(settings.objects(None, GA.destination))
        self.assertEqual(len(destinations), len(set(destinations)))

    def test_renderer_selection_uses_a_shared_rdf_resource(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        targets = set(settings.subjects(RDF.type, GA.Target))
        self.assertEqual(targets, {DOC.website, DOC.specification, DOC.pdf})
        for target in targets:
            with self.subTest(target=target):
                selectors = list(settings.objects(target, GA.renderer))
                self.assertEqual(len(selectors), 1)
                self.assertIsInstance(selectors[0], URIRef)

    def test_workflow_pins_one_dependabot_managed_grapharch_release(self):
        workflow = (ROOT / ".github/workflows/grapharch-reference.yml").read_text()
        pins = re.findall(r"uses: EKGF/grapharch@([0-9a-f]{40}) # v(\d+\.\d+\.\d+)\n",
                          workflow)
        self.assertEqual(len(pins), 1, workflow)
        self.assertIn("mode: install", workflow)
        self.assertNotIn("version:", workflow)
        self.assertNotIn("expected-revision:", workflow)
        dependabot = (ROOT / ".github/dependabot.yml").read_text()
        self.assertIn("package-ecosystem: github-actions", dependabot)
        self.assertIn("interval: daily", dependabot)
        self.assertIn("scripts/build_grapharch_pages.py", workflow)
        self.assertIn("_site/pages/static", workflow)

    def test_publication_uses_the_registered_family_name(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        registry = Graph().parse(ROOT / "dataset/well-known-families.ttl")
        names = [str(value) for value in registry.objects(FAMILY, RDFS.label)
                 if value.language == "en"]
        self.assertEqual(names, ["EKGF Ontologies"])
        for subject in (DOC.project, DOC.specification):
            self.assertEqual([str(value) for value in settings.objects(subject, DCTERMS.title)], names)

    def test_profile_and_publisher_resolve_to_existing_registry_entities(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        registry = Graph()
        for filename in ("well-known-authorities.ttl", "well-known-families.ttl",
                         "ekgf-family-references.ttl"):
            registry.parse(ROOT / "dataset" / filename)
        self.assertIn((DOC.profile, ARTPUB.publishesFamily, FAMILY), settings)
        self.assertIn((FAMILY, RDF.type, ARTGOV.Family), registry)
        self.assertIn((DOC.specification, GA.publisher, AUTHORITY), settings)
        self.assertIn((AUTHORITY, RDF.type, ARTGOV.Authority), registry)
        self.assertNotIn((FAMILY, RDF.type, ARTGOV.Family), settings)
        self.assertNotIn((AUTHORITY, RDF.type, ARTGOV.Authority), settings)
        self.assertTrue(list(registry.subjects(ARTGOV.inFamily, FAMILY)))

    def test_publication_project_is_separate_from_ontology_identities(self):
        settings = Graph().parse(ROOT / "publication/grapharch.ttl")
        self.assertIn((DOC.project, RDF.type, GA.Project), settings)
        ontologies = {subject for path in ROOT.glob("ekgf-*.ttl")
                      for subject in Graph().parse(path).subjects(
                          RDF.type, URIRef("http://www.w3.org/2002/07/owl#Ontology"))}
        self.assertTrue(ontologies)
        self.assertFalse(set(settings.subjects(RDF.type, GA.Project)) & ontologies)
