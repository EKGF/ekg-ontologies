"""Resource metadata belongs to the Annotation and Concept vocabularies."""
from pathlib import Path
import unittest
from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, XSD

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = Namespace('https://ekgf.org/ontology/annotation#')
CONCEPT = Namespace('https://ekgf.org/ontology/concept#')

class ResourceMetadataTests(unittest.TestCase):
    def test_properties_keep_their_datatype_semantics_and_new_ownership(self):
        for filename, prop, ontology in (
            ('ekgf-annotation.ttl', ANNOTATION.slug, URIRef(str(ANNOTATION))),
            ('ekgf-concept.ttl', CONCEPT.taxonomyKind, URIRef(str(CONCEPT))),
        ):
            graph = Graph().parse(ROOT / filename)
            self.assertIn((prop, RDF.type, OWL.DatatypeProperty), graph)
            self.assertIn((prop, RDFS.range, XSD.string), graph)
            self.assertIn((prop, RDFS.isDefinedBy, ontology), graph)
            self.assertTrue(list(graph.objects(prop, ANNOTATION.markdownDescription)))
            self.assertNotIn((prop, RDF.type, OWL.AnnotationProperty), graph)
            self.assertNotIn((prop, RDF.type, OWL.FunctionalProperty), graph)
            self.assertFalse(list(graph.objects(prop, RDFS.domain)))
            self.assertFalse(list(graph.objects(prop, OWL.equivalentProperty)))

    def test_api_ontology_and_its_registry_identity_are_removed(self):
        self.assertFalse((ROOT / 'ekgf-api.ttl').exists())
        retired = 'https://ekgf.org/ontology/' + 'api#'
        for path in [*ROOT.glob('ekgf-*.ttl'), *(ROOT / 'dataset').glob('*.ttl')]:
            graph = Graph().parse(path)
            for triple in graph:
                self.assertFalse(any(str(term).startswith(retired) for term in triple), path)
        registry = Graph().parse(ROOT / 'dataset/ekgf-family-references.ttl')
        self.assertFalse(list(registry.predicate_objects(URIRef('urn:uuid:f749fae7-72eb-4e1a-a35f-81eafbb4462a'))))

    def test_slug_references_are_moved_without_losing_registered_values(self):
        graph = Graph()
        for path in [*ROOT.glob('ekgf-*.ttl'), *(ROOT / 'dataset').glob('*.ttl')]:
            graph.parse(path)
        self.assertEqual(len(set(graph.subjects(ANNOTATION.slug, None))), 91)
        for filename in ('ekgf-artifact-governance.ttl', 'ekgf-use-case.ttl'):
            ontology = Graph().parse(ROOT / filename)
            self.assertIn((None, OWL.imports, URIRef(str(ANNOTATION))), ontology)
