"""Organization categories remain distinct from authority and community roles."""

import unittest

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import OWL

from test_governance_registry import (
    API, ARTGOV, ERROR, EX, ORG, PTS, ROLE, reason, turtle,
)


CLS = Namespace("https://www.omg.org/spec/Commons/Classifiers/")
DSG = Namespace("https://www.omg.org/spec/Commons/Designators/")


class OrganizationClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = turtle("ekgf-artifact-governance.ttl")
        cls.organizations = turtle("dataset/well-known-organizations.ttl")
        cls.authorities = turtle("dataset/well-known-authorities.ttl")

    def test_category_can_be_found_through_the_authority_player(self):
        data = self.organizations + self.authorities
        expected = {
            "w3c": {ARTGOV.StandardsBodyCategory, ARTGOV.ConsortiumCategory},
            "omg": {ARTGOV.StandardsBodyCategory, ARTGOV.ConsortiumCategory},
            "spdx": {ARTGOV.ProjectCategory},
            "ekgf": {ARTGOV.CommunityCategory},
        }
        for slug, categories in expected.items():
            with self.subTest(slug=slug):
                authority = data.value(predicate=API.slug, object=Literal(slug), any=False)
                self.assertIsNotNone(authority)
                actual = set(data.objects(
                    authority, ROLE.isPlayedBy / ARTGOV.organizationCategory
                ))
                self.assertTrue(categories <= actual, (slug, actual))

    def test_registered_categories_classify_organizations_only(self):
        assignments = list(self.organizations.subject_objects(ARTGOV.organizationCategory))
        self.assertTrue(assignments)
        self.assertFalse(list(self.authorities.triples((None, ARTGOV.organizationCategory, None))))
        for organization, category in assignments:
            with self.subTest(organization=organization, category=category):
                self.assertIn((organization, RDF.type, ORG.Organization), self.organizations)
                self.assertIn((category, RDF.type, ARTGOV.OrganizationCategory), self.ontology)
                self.assertNotIn((category, RDF.type, OWL.Class), self.ontology)

    def test_classifiers_belong_to_an_explicit_nonexclusive_scheme(self):
        scheme = ARTGOV.OrganizationCategoryScheme
        self.assertIn((scheme, RDF.type, CLS.ClassificationScheme), self.ontology)
        self.assertIn((scheme, CLS.isExclusive, Literal(False)), self.ontology)
        categories = set(self.ontology.subjects(RDF.type, ARTGOV.OrganizationCategory))
        self.assertTrue(categories)
        for category in categories:
            with self.subTest(category=category):
                self.assertIn((category, DSG.isDefinedIn, scheme), self.ontology)
                self.assertTrue(list(self.ontology.objects(category, RDFS.label)))
                self.assertTrue(list(self.ontology.objects(category, RDFS.comment)))

    def test_commons_queries_see_the_categories_without_creating_roles(self):
        graph = reason(self.organizations)
        assignments = list(self.organizations.subject_objects(ARTGOV.organizationCategory))
        self.assertTrue(assignments)
        for organization, category in assignments:
            with self.subTest(organization=organization, category=category):
                self.assertIn((organization, CLS.isClassifiedBy, category), graph)
                self.assertIn((category, CLS.classifies, organization), graph)
                self.assertIn((category, RDF.type, CLS.Classifier), graph)
                self.assertNotIn((organization, RDF.type, ROLE.Role), graph)
                self.assertNotIn((category, RDF.type, ROLE.Role), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_one_legal_entity_can_have_multiple_categories(self):
        data = Graph()
        data.add((EX.organization, RDF.type, ORG.LegalEntity))
        for category in (ARTGOV.StandardsBodyCategory, ARTGOV.ConsortiumCategory):
            data.add((EX.organization, ARTGOV.organizationCategory, category))
        data.add((ARTGOV.StandardsBodyCategory, OWL.differentFrom, ARTGOV.ConsortiumCategory))
        graph = reason(data)
        self.assertFalse(list(graph.objects(None, ERROR)))
        self.assertIn((EX.organization, RDF.type, ORG.LegalEntity), graph)
        self.assertIn((EX.organization, RDF.type, PTS.Agent), graph)
        self.assertNotIn((EX.organization, RDF.type, ARTGOV.Authority), graph)

    def test_category_on_an_authority_conflicts_with_commons_role_separation(self):
        data = Graph()
        data.add((EX.authority, RDF.type, ARTGOV.Authority))
        data.add((EX.authority, ARTGOV.organizationCategory, ARTGOV.StandardsBodyCategory))
        self.assertTrue(list(reason(data).objects(None, ERROR)))

    def test_publishing_and_community_roles_cannot_be_organization_categories(self):
        for role in (ARTGOV.AuthorityPublisherRole, ARTGOV.StandardsEditorRole):
            with self.subTest(role=role):
                data = Graph()
                data.add((EX.organization, RDF.type, ORG.Organization))
                data.add((EX.organization, ARTGOV.organizationCategory, role))
                self.assertTrue(list(reason(data).objects(None, ERROR)))


if __name__ == "__main__":
    unittest.main()
