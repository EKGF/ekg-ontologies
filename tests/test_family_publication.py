"""Optional family grouping; versions and approvals belong to releases."""

import unittest

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import XSD

from test_governance_registry import ARTGOV, ERROR, EX, ORG, reason, turtle


ARTPUB = Namespace("https://ekgf.org/ontology/artifact-publication#")
LIFECYCLE = Namespace("https://ekgf.org/ontology/lifecycle#")
PUBLICATION = Namespace("https://ekgf.org/lifecycle/publication#")


def publication_data():
    graph = Graph()
    graph.add((EX.family, RDF.type, ARTGOV.Family))
    graph.add((EX.authority, RDF.type, ARTGOV.Authority))
    graph.add((EX.profile, RDF.type, ARTPUB.PublicationProfile))
    graph.add((EX.profile, ARTPUB.publishesFamily, EX.family))
    for release, version, commit, state in (
        (EX.release1, "1.0", "commit-one", PUBLICATION.Superseded),
        (EX.release2, "2.0", "commit-two", PUBLICATION.ReleaseCandidate),
    ):
        graph.add((release, RDF.type, ARTPUB.StandardsRelease))
        graph.add((release, ARTPUB.releaseFamily, EX.family))
        graph.add((release, ARTPUB.releaseVersion, Literal(version)))
        graph.add((release, ARTPUB.inputCommitCid, Literal(commit)))
        graph.add((release, ARTPUB.publicationProfile, EX.profile))
        graph.add((release, LIFECYCLE.hasState, state))
    graph.add((EX.approval, RDF.type, ARTPUB.ReleaseApproval))
    graph.add((EX.approval, ARTPUB.approvesRelease, EX.release1))
    graph.add((EX.approval, ARTPUB.approvedBy, EX.authority))
    graph.add((EX.approval, ARTPUB.approvedAt,
               Literal("2026-10-01T09:00:00Z", datatype=XSD.dateTime)))
    return graph


def ungrouped_publication_data():
    graph = publication_data()
    graph.remove((EX.family, None, None))
    graph.remove((None, ARTPUB.publishesFamily, None))
    graph.remove((None, ARTPUB.releaseFamily, None))
    for reference, artifact in ((EX.ontologyReference, EX.ontology),
                                (EX.shapesReference, EX.shapes)):
        graph.add((reference, RDF.type, ARTGOV.Reference))
        graph.add((reference, ARTGOV.refersTo, artifact))
        graph.add((reference, ARTGOV.governedBy, EX.authority))
        graph.add((EX.profile, ARTPUB.publishesReference, reference))
        for release in (EX.release1, EX.release2):
            graph.add((release, ARTPUB.releaseReference, reference))
    return graph


class FamilyPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = turtle("ekgf-artifact-publication.ttl")

    def assert_conforms(self, data, expected):
        conforms, _, report = validate(data, shacl_graph=self.ontology)
        self.assertEqual(conforms, expected, report)

    def test_release_and_approval_links_have_distinct_semantics(self):
        data = Graph()
        data.add((EX.release, ARTPUB.releaseFamily, EX.family))
        data.add((EX.approval, ARTPUB.approvesRelease, EX.release))
        data.add((EX.approval, ARTPUB.approvedBy, EX.authority))
        graph = reason(data + self.ontology)
        for resource, expected_type in (
            (EX.release, ARTPUB.StandardsRelease),
            (EX.family, ARTGOV.Family),
            (EX.approval, ARTPUB.ReleaseApproval),
            (EX.authority, ARTGOV.Authority),
        ):
            with self.subTest(resource=resource):
                self.assertIn((resource, RDF.type, expected_type), graph)
        self.assertNotIn((EX.release, RDF.type, ARTPUB.PublicationProfile), graph)
        self.assertFalse(list(graph.objects(None, ERROR)))

    def test_version_cannot_be_put_on_the_enduring_family(self):
        data = Graph()
        data.add((EX.family, RDF.type, ARTGOV.Family))
        data.add((EX.family, ARTPUB.releaseVersion, Literal("1.0")))
        self.assertTrue(list(reason(data + self.ontology).objects(None, ERROR)))

    def test_approval_does_not_transfer_to_another_release_or_publish_it(self):
        data = publication_data()
        self.assert_conforms(data, True)
        graph = reason(data + self.ontology)
        self.assertEqual(set(graph.objects(EX.approval, ARTPUB.approvesRelease)),
                         {EX.release1})
        self.assertEqual(set(graph.objects(EX.release1, LIFECYCLE.hasState)),
                         {PUBLICATION.Superseded})
        self.assertNotIn((EX.family, RDF.type, ARTPUB.StandardsRelease), graph)
        self.assertNotIn((EX.family, ARTPUB.releaseVersion, Literal("1.0")), graph)

    def test_several_authorities_can_approve_the_same_release_separately(self):
        data = publication_data()
        data.add((EX.otherAuthority, RDF.type, ARTGOV.Authority))
        for predicate, value in list(data.predicate_objects(EX.approval)):
            data.add((EX.otherApproval, predicate,
                      EX.otherAuthority if predicate == ARTPUB.approvedBy else value))
        self.assert_conforms(data, True)

    def test_publication_and_approval_work_without_any_family(self):
        data = ungrouped_publication_data()
        self.assert_conforms(data, True)
        graph = reason(data + self.ontology)
        self.assertFalse(list(graph.subjects(RDF.type, ARTGOV.Family)))
        self.assertFalse(list(graph.objects(None, ARTGOV.inFamily)))
        self.assertEqual(set(graph.objects(EX.approval, ARTPUB.approvesRelease)),
                         {EX.release1})

    def test_release_requires_one_scope_and_one_version(self):
        for predicate, extra in (
            (ARTPUB.releaseFamily, EX.otherFamily),
            (ARTPUB.releaseVersion, Literal("other-version")),
        ):
            for count in (0, 2):
                with self.subTest(predicate=predicate, count=count):
                    data = publication_data()
                    data.add((EX.otherFamily, RDF.type, ARTGOV.Family))
                    if count == 0:
                        data.remove((EX.release1, predicate, None))
                    else:
                        data.add((EX.release1, predicate, extra))
                    self.assert_conforms(data, False)

    def test_release_can_be_recorded_without_a_local_generator_run_or_commit(self):
        data = ungrouped_publication_data()
        data.remove((None, ARTPUB.inputCommitCid, None))
        data.remove((None, ARTPUB.publicationProfile, None))
        self.assert_conforms(data, True)

    def test_release_cannot_mix_family_and_individual_reference_scopes(self):
        for subject, predicate in ((EX.release1, ARTPUB.releaseReference),
                                   (EX.profile, ARTPUB.publishesReference)):
            with self.subTest(predicate=predicate):
                data = publication_data()
                data.add((EX.reference, RDF.type, ARTGOV.Reference))
                data.add((subject, predicate, EX.reference))
                self.assert_conforms(data, False)

    def test_missing_release_type_does_not_bypass_validation(self):
        data = publication_data()
        data.remove((EX.release1, RDF.type, ARTPUB.StandardsRelease))
        data.remove((EX.release1, ARTPUB.releaseFamily, None))
        self.assert_conforms(data, False)

    def test_family_scoped_profile_requires_exactly_one_family(self):
        for count in (0, 2):
            with self.subTest(count=count):
                data = publication_data()
                if count == 0:
                    data.remove((EX.profile, ARTPUB.publishesFamily, None))
                else:
                    data.add((EX.otherFamily, RDF.type, ARTGOV.Family))
                    data.add((EX.profile, ARTPUB.publishesFamily, EX.otherFamily))
                self.assert_conforms(data, False)

    def test_profile_and_release_must_identify_the_same_family(self):
        data = publication_data()
        data.add((EX.otherFamily, RDF.type, ARTGOV.Family))
        data.set((EX.profile, ARTPUB.publishesFamily, EX.otherFamily))
        self.assert_conforms(data, False)

    def test_profile_and_release_must_identify_the_same_references(self):
        for subject, predicate in ((EX.release1, ARTPUB.releaseReference),
                                   (EX.profile, ARTPUB.publishesReference)):
            with self.subTest(predicate=predicate):
                data = ungrouped_publication_data()
                data.remove((subject, predicate, EX.shapesReference))
                self.assert_conforms(data, False)

    def test_ungrouped_release_requires_at_least_one_reference(self):
        for subject, predicate in ((EX.release1, ARTPUB.releaseReference),
                                   (EX.profile, ARTPUB.publishesReference)):
            with self.subTest(predicate=predicate):
                data = ungrouped_publication_data()
                data.remove((subject, predicate, None))
                self.assert_conforms(data, False)

    def test_linked_run_must_match_the_release_commit_and_family(self):
        for mismatch in (None, "commit", "family", "missing-commit"):
            with self.subTest(mismatch=mismatch):
                data = publication_data()
                data.add((EX.release1, ARTPUB.publicationRun, EX.run))
                data.add((EX.run, RDF.type, ARTPUB.PublicationRun))
                data.add((EX.run, ARTPUB.inputCommitCid, Literal("commit-one")))
                data.add((EX.run, ARTPUB.publicationProfile, EX.runProfile))
                data.add((EX.runProfile, RDF.type, ARTPUB.PublicationProfile))
                data.add((EX.runProfile, ARTPUB.publishesFamily, EX.family))
                if mismatch == "commit":
                    data.set((EX.run, ARTPUB.inputCommitCid, Literal("wrong-commit")))
                elif mismatch == "family":
                    data.add((EX.otherFamily, RDF.type, ARTGOV.Family))
                    data.set((EX.runProfile, ARTPUB.publishesFamily, EX.otherFamily))
                elif mismatch == "missing-commit":
                    data.remove((EX.run, ARTPUB.inputCommitCid, None))
                self.assert_conforms(data, mismatch is None)

    def test_approval_requires_one_release_authority_and_timestamp(self):
        for predicate, extra in (
            (ARTPUB.approvesRelease, EX.release2),
            (ARTPUB.approvedBy, EX.otherAuthority),
            (ARTPUB.approvedAt, Literal("2026-10-02T09:00:00Z", datatype=XSD.dateTime)),
        ):
            for count in (0, 2):
                with self.subTest(predicate=predicate, count=count):
                    data = publication_data()
                    data.add((EX.otherAuthority, RDF.type, ARTGOV.Authority))
                    if count == 0:
                        data.remove((EX.approval, predicate, None))
                    else:
                        data.add((EX.approval, predicate, extra))
                    self.assert_conforms(data, False)

    def test_approval_cannot_target_a_family_or_name_an_organization_as_authority(self):
        for predicate, value in (
            (ARTPUB.approvesRelease, EX.family),
            (ARTPUB.approvedBy, EX.organization),
            (ARTPUB.approvedAt, Literal("yesterday")),
        ):
            with self.subTest(predicate=predicate):
                data = publication_data()
                data.add((EX.organization, RDF.type, ORG.Organization))
                data.set((EX.approval, predicate, value))
                self.assert_conforms(data, False)

    def test_family_cannot_also_be_a_release_even_if_all_fields_are_present(self):
        data = publication_data()
        data.add((EX.release1, RDF.type, ARTGOV.Family))
        self.assert_conforms(data, False)


if __name__ == "__main__":
    unittest.main()
