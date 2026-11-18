"""Families can have explicit, nested modules; resources can have short titles."""

from pathlib import Path
import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.namespace import XSD


ROOT = Path(__file__).resolve().parents[1]
ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
ANNOTATION = Namespace("https://ekgf.org/ontology/annotation#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.test/")


class ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-artifact-governance.ttl")

    def assert_valid(self, data, expected=True, inference="rdfs"):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference=inference, do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def family(self, data=None, family=EX.fibo, modules=(EX.fbc,)):
        data = Graph() if data is None else data
        data.add((family, RDF.type, ARTGOV.Family))
        for module in modules:
            data.add((module, RDF.type, ARTGOV.Module))
            data.add((module, RDFS.label, Literal(str(module).rsplit("/", 1)[1].upper(), lang="en")))
            data.add((module, ARTGOV.inFamily, family))
        return data

    def test_module_terms_are_declared_and_documented(self):
        self.assertIn((ARTGOV.Module, RDF.type, OWL.Class), self.ontology)
        self.assertIn((ARTGOV.inModule, RDF.type, OWL.ObjectProperty), self.ontology)
        self.assertIn((ARTGOV.inModule, RDFS.range, ARTGOV.Module), self.ontology)
        for disjoint in (ARTGOV.Family, ARTGOV.Reference, ARTGOV.Authority):
            self.assertIn((ARTGOV.Module, OWL.disjointWith, disjoint), self.ontology)
        for term in (ARTGOV.Module, ARTGOV.inModule):
            self.assertTrue(list(self.ontology.objects(term, ANNOTATION.markdownDescription)))

    def test_artifacts_and_references_join_a_module_of_their_family(self):
        data = self.family()
        data.add((EX.accounting, ARTGOV.inModule, EX.fbc))
        data.add((EX.accounting, ARTGOV.inFamily, EX.fibo))
        data.add((EX.reference, RDF.type, ARTGOV.Reference))
        data.add((EX.reference, ARTGOV.inModule, EX.fbc))
        self.assert_valid(data)

    def test_modules_nest_within_one_family(self):
        data = self.family(modules=(EX.fnd, EX.utilities))
        data.add((EX.utilities, ARTGOV.inModule, EX.fnd))
        data.add((EX.annotations, ARTGOV.inModule, EX.utilities))
        self.assert_valid(data)
        rows = data.query("""
            PREFIX artgov: <https://ekgf.org/ontology/artifact-governance#>
            PREFIX ex: <https://example.test/>
            SELECT ?module WHERE { ex:annotations artgov:inModule+ ?module }
        """)
        self.assertEqual({row.module for row in rows}, {EX.utilities, EX.fnd})

    def test_a_module_needs_exactly_one_family_and_a_label(self):
        data = self.family()
        data.remove((EX.fbc, ARTGOV.inFamily, EX.fibo))
        self.assert_valid(data, False)
        data = self.family()
        data.add((EX.fbc, ARTGOV.inFamily, EX.other))
        data.add((EX.other, RDF.type, ARTGOV.Family))
        self.assert_valid(data, False)
        data = self.family()
        data.remove((EX.fbc, RDFS.label, None))
        self.assert_valid(data, False)

    def test_a_member_declaring_families_must_include_its_module_family(self):
        data = self.family()
        data.add((EX.other, RDF.type, ARTGOV.Family))
        data.add((EX.accounting, ARTGOV.inModule, EX.fbc))
        data.add((EX.accounting, ARTGOV.inFamily, EX.other))
        self.assert_valid(data, False)
        data.add((EX.accounting, ARTGOV.inFamily, EX.fibo))
        self.assert_valid(data)

    def test_a_nested_module_must_share_its_parent_family(self):
        data = self.family(modules=(EX.fnd,))
        self.family(data, family=EX.commons, modules=(EX.identifiers,))
        data.add((EX.identifiers, ARTGOV.inModule, EX.fnd))
        self.assert_valid(data, False)

    def test_a_member_has_at_most_one_direct_module(self):
        data = self.family(modules=(EX.fbc, EX.sec))
        data.add((EX.accounting, ARTGOV.inModule, EX.fbc))
        data.add((EX.accounting, ARTGOV.inModule, EX.sec))
        self.assert_valid(data, False)

    def test_module_nesting_must_be_acyclic(self):
        data = self.family(modules=(EX.fnd, EX.utilities))
        data.add((EX.utilities, ARTGOV.inModule, EX.fnd))
        data.add((EX.fnd, ARTGOV.inModule, EX.utilities))
        self.assert_valid(data, False)

    def test_modules_are_not_families_references_or_authorities(self):
        for kind in (ARTGOV.Family, ARTGOV.Reference, ARTGOV.Authority):
            with self.subTest(kind=kind):
                data = self.family()
                data.add((EX.fbc, RDF.type, kind))
                self.assert_valid(data, False)

    def test_module_values_must_be_iris_without_inference_too(self):
        data = self.family()
        data.add((EX.accounting, ARTGOV.inModule, Literal("FBC")))
        self.assert_valid(data, False)
        data = self.family()
        data.add((EX.accounting, ARTGOV.inModule, EX.fbc))
        self.assert_valid(data, inference="none")

    def test_validators_are_in_the_ontology_shapes_graph(self):
        for shape in (ARTGOV.ModuleShape, ARTGOV.ModuleMembershipShape):
            self.assertIn((shape, RDF.type, SH.NodeShape), self.ontology)
        self.assertIn((URIRef(str(ARTGOV)), RDF.type, SH.ShapesGraph), self.ontology)


class ShortTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-annotation.ttl")

    def assert_valid(self, data, expected=True):
        conforms, _, report = validate(
            data, shacl_graph=self.ontology, ont_graph=self.ontology,
            inference="none", do_owl_imports=False,
        )
        self.assertEqual(conforms, expected, report)

    def test_short_title_is_a_documented_annotation_property(self):
        self.assertIn((ANNOTATION.shortTitle, RDF.type, OWL.AnnotationProperty), self.ontology)
        self.assertTrue(list(self.ontology.objects(ANNOTATION.shortTitle, RDFS.comment)))
        self.assertTrue(list(self.ontology.objects(ANNOTATION.shortTitle,
                                                   ANNOTATION.markdownDescription)))
        self.assertIn((ANNOTATION.ShortTitleShape, RDF.type, SH.NodeShape), self.ontology)
        self.assertIn((URIRef(str(ANNOTATION)), RDF.type, SH.ShapesGraph), self.ontology)

    def test_one_short_title_per_language(self):
        data = Graph()
        data.add((EX.identifiers, ANNOTATION.shortTitle, Literal("Identifiers Ontology", lang="en")))
        data.add((EX.identifiers, ANNOTATION.shortTitle, Literal("Identificatie-ontologie", lang="nl")))
        self.assert_valid(data)
        data.add((EX.identifiers, ANNOTATION.shortTitle, Literal("Identifiers", lang="en")))
        self.assert_valid(data, False)

    def test_short_titles_need_a_language_tag_and_text(self):
        for value in (Literal("Identifiers Ontology"), Literal("", lang="en"),
                      Literal("Identifiers Ontology", datatype=XSD.string), EX.title):
            with self.subTest(value=value):
                data = Graph()
                data.add((EX.identifiers, ANNOTATION.shortTitle, value))
                self.assert_valid(data, False)



class SortKeyTests(unittest.TestCase):
    def test_sort_key_is_a_string_hint_that_falls_back_to_the_label(self):
        ontology = Graph().parse(ROOT / "ekgf-annotation.ttl")
        self.assertIn((ANNOTATION.sortKey, RDF.type, OWL.DatatypeProperty), ontology)
        self.assertIn((ANNOTATION.sortKey, RDFS.range, XSD.string), ontology)
        self.assertFalse(list(ontology.objects(ANNOTATION.sortKey, RDFS.domain)))
        definition, = ontology.objects(ANNOTATION.sortKey, RDFS.comment)
        for phrase in ("in place of its label", "sorts by its label", "a hint, not a rank"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, str(definition))
        self.assertTrue(list(ontology.objects(ANNOTATION.sortKey, ANNOTATION.markdownDescription)))

if __name__ == "__main__":
    unittest.main()
