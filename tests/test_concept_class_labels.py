"""Concept vocabulary classes have canonical English display labels."""

from pathlib import Path
import unittest

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef


ROOT = Path(__file__).resolve().parents[1]
CONCEPT = Namespace("https://ekgf.org/ontology/concept#")

CLASS_LABELS = {
    "DataElementConcept": "Data Element Concept",
    "ConceptSet": "Concept Set",
    "ConceptManifestation": "Concept Manifestation",
    "BusinessTerm": "Business Term",
    "Abbreviation": "Abbreviation",
    "FullSingularBusinessTerm": "Full Singular Business Term",
    "FullPluralBusinessTerm": "Full Plural Business Term",
    "Tagline": "Tagline",
    "Description": "Description",
    "TechnicalManifestation": "Technical Manifestation",
    "URIParameterManifestation": "URI Parameter Manifestation",
    "SPARQLVariableManifestation": "SPARQL Variable Manifestation",
    "SPARQLResultColumnManifestation": "SPARQL Result Column Manifestation",
    "TemplateParameterManifestation": "Template Parameter Manifestation",
    "TemplateLanguage": "Template Language",
    "OWLClassManifestation": "OWL Class Manifestation",
    "OWLPropertyManifestation": "OWL Property Manifestation",
    "OWLAxiomManifestation": "OWL Axiom Manifestation",
    "OWLNamedIndividualManifestation": "OWL Named Individual Manifestation",
    "SHACLShapeManifestation": "SHACL Shape Manifestation",
    "SHACLShapeSetManifestation": "SHACL Shape Set Manifestation",
    "SKOSConceptManifestation": "SKOS Concept Manifestation",
    "SKOSConceptSchemeManifestation": "SKOS Concept Scheme Manifestation",
    "LiteralDatatypeManifestation": "Literal Datatype Manifestation",
    "RDFPredicateManifestation": "RDF Predicate Manifestation",
    "RDFSClassManifestation": "RDFS Class Manifestation",
    "RawSourceFieldManifestation": "Raw Source Field Manifestation",
    "SQLTableManifestation": "SQL Table Manifestation",
    "SQLColumnManifestation": "SQL Column Manifestation",
    "CypherIdentifierManifestation": "Cypher Identifier Manifestation",
    "SourceCodeIdentifierManifestation": "Source Code Identifier Manifestation",
    "JavaScriptIdentifierManifestation": "JavaScript Identifier Manifestation",
    "PythonIdentifierManifestation": "Python Identifier Manifestation",
    "JavaIdentifierManifestation": "Java Identifier Manifestation",
    "JSONFieldManifestation": "JSON Field Manifestation",
    "ManifestationOccurrence": "Manifestation Occurrence",
    "StatementPosition": "Statement Position",
}


class ConceptClassLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = Graph().parse(ROOT / "ekgf-concept.ttl", format="turtle")

    def test_all_owned_classes_have_canonical_english_display_labels(self):
        classes = {term for term in self.ontology.subjects(RDF.type, OWL.Class)
                   if isinstance(term, URIRef) and str(term).startswith(str(CONCEPT))}
        self.assertEqual(classes, {CONCEPT[name] for name in CLASS_LABELS})
        for name, label in CLASS_LABELS.items():
            with self.subTest(name=name):
                labels = {value for value in self.ontology.objects(CONCEPT[name], RDFS.label)
                          if isinstance(value, Literal) and value.language == "en"}
                self.assertEqual(labels, {Literal(label, lang="en")})


if __name__ == "__main__":
    unittest.main()
