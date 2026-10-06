"""Registry identity and Commons role semantics, without network access."""

from pathlib import Path
import unittest
from urllib.parse import urlsplit
from uuid import RFC_4122, UUID

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import OWL, XSD


ROOT = Path(__file__).resolve().parents[1]
ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
API = Namespace("https://ekgf.org/ontology/api#")
ORG = Namespace("https://www.omg.org/spec/Commons/Organizations/")
PTS = Namespace("https://www.omg.org/spec/Commons/PartiesAndSituations/")
ROLE = Namespace("https://www.omg.org/spec/Commons/RolesAndCompositions/")
EX = Namespace("https://example.test/")
ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


def turtle(path):
    return Graph().parse(ROOT / path, format="turtle")


def reason(data):
    graph = turtle("ekgf-artifact-governance.ttl")
    graph += turtle("tests/fixtures/commons-role-semantics.ttl.txt")
    graph += data
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    return graph


class GovernanceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authorities = turtle("dataset/well-known-authorities.ttl")
        cls.ontology = turtle("ekgf-artifact-governance.ttl")
        cls.dataset = Graph()
        for path in sorted((ROOT / "dataset").glob("*.ttl")):
            cls.dataset.parse(path, format="turtle")

    def assert_uuid4(self, resource):
        self.assertIsInstance(resource, URIRef)
        self.assertTrue(str(resource).startswith("urn:uuid:"), resource)
        value = UUID(str(resource).removeprefix("urn:uuid:"))
        self.assertEqual(value.variant, RFC_4122, resource)
        self.assertEqual(value.version, 4, resource)
        self.assertEqual(value.urn, str(resource))

    def test_authorities_have_random_uuid_identifiers(self):
        authorities = set(self.authorities.subjects(RDF.type, ARTGOV.Authority))
        self.assertTrue(authorities)
        for authority in authorities:
            with self.subTest(authority=authority):
                self.assert_uuid4(authority)

    def test_organizations_have_separate_registered_identities(self):
        organizations = turtle("dataset/well-known-organizations.ttl")
        identities = set(organizations.subjects(RDF.type, ORG.Organization))
        self.assertTrue(identities)
        for organization in identities:
            with self.subTest(organization=organization):
                self.assert_uuid4(organization)
                self.assertNotIn((organization, RDF.type, ARTGOV.Authority), self.dataset)
        players = set(self.authorities.objects(None, ROLE.isPlayedBy))
        self.assertTrue(players)
        self.assertTrue(players <= identities, players - identities)
        for authority, organization in self.authorities.subject_objects(ROLE.isPlayedBy):
            self.assertNotEqual(authority, organization)

    def test_governance_references_resolve_to_registered_authorities(self):
        authorities = set(self.authorities.subjects(RDF.type, ARTGOV.Authority))
        references = set(self.dataset.objects(None, ARTGOV.governedBy))
        self.assertTrue(references)
        self.assertTrue(references <= authorities, references - authorities)

    def test_ekgf_references_cover_exactly_the_local_ontologies(self):
        ontology_iris = set()
        for path in ROOT.glob("ekgf-*.ttl"):
            ontology_iris.update(turtle(path).subjects(RDF.type, OWL.Ontology))
        references = turtle("dataset/ekgf-family-references.ttl")
        covered = set()
        for reference in references.subjects(RDF.type, ARTGOV.Reference):
            with self.subTest(reference=reference):
                targets = set(references.objects(reference, ARTGOV.refersTo))
                local_targets = targets & ontology_iris
                self.assertEqual(len(local_targets), 1,
                                 f"Reference must identify one local ontology: {targets}")
                covered.update(local_targets)
        self.assertEqual(covered, ontology_iris)

    def test_organization_relationships_resolve_to_registered_organizations(self):
        organizations = set(self.dataset.subjects(RDF.type, ORG.Organization))
        for predicate in (ARTGOV.legalOwner, ARTGOV.communityOrganization, ORG.isSubUnitOf):
            for subject, target in self.dataset.subject_objects(predicate):
                with self.subTest(subject=subject, predicate=predicate):
                    self.assertIn(target, organizations)
                    self.assertNotEqual(subject, target)

    def test_registered_roles_and_organizations_are_consistent(self):
        graph = reason(self.dataset)
        self.assertFalse(list(graph.objects(None, ERROR)))
        for authority in self.authorities.subjects(RDF.type, ARTGOV.Authority):
            with self.subTest(authority=authority):
                self.assertIn((authority, RDF.type, PTS.PartyRole), graph)
                self.assertNotIn((authority, RDF.type, PTS.Agent), graph)

    def test_base_iris_support_multiple_registered_hosts(self):
        for authority in self.authorities.subjects(RDF.type, ARTGOV.Authority):
            with self.subTest(authority=authority):
                hosts = {
                    str(value)
                    for value in self.authorities.objects(authority, ARTGOV.authorityHost)
                }
                self.assertTrue(hosts)
                for base in self.authorities.objects(authority, ARTGOV.baseIri):
                    self.assertIn(urlsplit(str(base)).hostname, hosts)
        topquadrant = next(
            self.authorities.subjects(API.slug, Literal("topquadrant"))
        )
        self.assertGreaterEqual(
            len(set(self.authorities.objects(topquadrant, ARTGOV.authorityHost))), 2
        )

    def test_commons_imports_supply_the_organization_and_role_model(self):
        imports = set(self.ontology.objects(URIRef(str(ARTGOV)), OWL.imports))
        self.assertTrue(
            {URIRef(str(ORG)), URIRef(str(PTS)), URIRef(str(ROLE))} <= imports
        )
        self.assertNotIn(URIRef("http://www.w3.org/ns/org#"), imports)

    def test_an_authority_is_a_role_even_without_a_known_player(self):
        data = Graph()
        data.add((EX.authority, RDF.type, ARTGOV.Authority))
        graph = reason(data)
        self.assertIn((EX.authority, RDF.type, PTS.PartyRole), graph)
        self.assertIn((EX.authority, RDF.type, ROLE.Role), graph)
        self.assertNotIn((EX.authority, RDF.type, ORG.Organization), graph)

    def test_an_authority_cannot_be_its_own_organization(self):
        data = Graph()
        data.add((EX.authority, RDF.type, ARTGOV.Authority))
        data.add((EX.authority, RDF.type, ORG.Organization))
        graph = reason(data)
        self.assertTrue(
            list(graph.objects(None, ERROR)), "Expected Commons disjointness violation"
        )

    def test_one_organization_can_play_several_authority_roles(self):
        data = Graph()
        data.add((EX.organization, RDF.type, ORG.Organization))
        data.add((EX.first, OWL.differentFrom, EX.second))
        for authority in (EX.first, EX.second):
            data.add((authority, RDF.type, ARTGOV.Authority))
            data.add((authority, ROLE.isPlayedBy, EX.organization))
        graph = reason(data)
        self.assertFalse(list(graph.objects(None, ERROR)))
        self.assertNotIn((EX.first, OWL.sameAs, EX.second), graph)
        self.assertNotIn((EX.organization, RDF.type, ROLE.Role), graph)

    def test_changing_and_sharing_hosts_does_not_merge_identities(self):
        data = Graph()
        for authority in (EX.first, EX.second):
            data.add((authority, RDF.type, ARTGOV.Authority))
            data.add((authority, ARTGOV.authorityHost, Literal("shared.example")))
            data.add((
                authority,
                ARTGOV.baseIri,
                Literal("https://shared.example/", datatype=XSD.anyURI),
            ))
        data.add((EX.first, OWL.differentFrom, EX.second))
        data.add((EX.first, ARTGOV.authorityHost, Literal("new.example")))
        graph = reason(data)
        self.assertFalse(list(graph.objects(None, ERROR)))
        self.assertNotIn((EX.first, OWL.sameAs, EX.second), graph)
        self.assertIn((EX.first, ARTGOV.authorityHost, Literal("new.example")), graph)


if __name__ == "__main__":
    unittest.main()
