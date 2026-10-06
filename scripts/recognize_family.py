"""Reference implementation of the artifact-governance recognition contract."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD


ARTGOV = Namespace("https://ekgf.org/ontology/artifact-governance#")
PREFIX_METHODS = (ARTGOV.namespaceIriPrefix, ARTGOV.filePathPrefix, ARTGOV.graphIriPrefix)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class RecognitionError(ValueError):
    """Invalid registry data or conflicting family recognition evidence."""


@dataclass(frozen=True)
class FamilyRecognition:
    families: tuple[URIRef, ...]
    basis: str


def _absolute_iri(value):
    return bool(SCHEME.match(value)) and not re.search(r'[\s<>"{}|^`\\]', value)


def _require_family(data, family):
    if not isinstance(family, URIRef) or (family, RDF.type, ARTGOV.Family) not in data:
        raise RecognitionError(f"Unregistered family: {family}")


def _prefix_rules(data):
    rules = {}
    for method in PREFIX_METHODS:
        rules[method] = []
        for family, value in data.subject_objects(method):
            _require_family(data, family)
            if not isinstance(value, Literal) or value.language:
                raise RecognitionError(f"Expected a typed prefix literal for {family} {method}")
            prefix = str(value)
            if method == ARTGOV.filePathPrefix:
                segments = prefix.removesuffix("/").split("/")
                valid = (
                    value.datatype in (None, XSD.string)
                    and bool(prefix) and not prefix.startswith("/")
                    and not any(character in prefix for character in ("\\", ":", "\x00", "\n", "\r"))
                    and not any(segment in ("", ".", "..") for segment in segments)
                )
            else:
                valid = value.datatype == XSD.anyURI and _absolute_iri(prefix)
            if not valid:
                raise RecognitionError(f"Invalid {method.split('#')[-1]} for {family}: {value.n3()}")
            rules[method].append((family, prefix))
    return rules


def _source_path(value):
    path = value.replace("\\", "/")
    if not path or "\x00" in path or "\n" in path or "\r" in path:
        raise RecognitionError("The source path must be a nonempty file path")
    if SCHEME.match(path) and not re.match(r"^[A-Za-z]:/", path):
        raise RecognitionError("Pass a file path as source_path, not a source URI")
    segments = path.split("/")
    if ".." in segments:
        raise RecognitionError("Resolve parent-directory segments before supplying the source path")
    normalized = "/".join(segment for segment in segments if segment not in ("", "."))
    if not normalized:
        raise RecognitionError("The source path must identify a file")
    return normalized


def _explicit_families(data, artifact):
    pending, visited, families = [artifact], set(), set()
    while pending:
        subject = pending.pop()
        if subject in visited:
            continue
        visited.add(subject)
        for family in data.objects(subject, ARTGOV.inFamily):
            _require_family(data, family)
            families.add(family)
        # References connect the known IRI aliases of one artifact.
        pending.extend(data.subjects(ARTGOV.refersTo, subject))
        pending.extend(data.objects(subject, ARTGOV.refersTo))
    return families


def recognize_family(data, artifact_iri, *, source_path=None, graph_iri=None):
    """Resolve one artifact using asserted memberships or independent prefix methods.

    `data` contains family declarations, prefix rules and any explicit membership
    or reference records. It is never modified. Paths are supplied separately
    from named-graph IRIs; no path is guessed from a graph name.
    """
    if not _absolute_iri(artifact_iri):
        raise RecognitionError(f"Expected an absolute artifact IRI: {artifact_iri}")
    if graph_iri is not None and not _absolute_iri(graph_iri):
        raise RecognitionError(f"Expected an absolute graph IRI: {graph_iri}")
    path = _source_path(source_path) if source_path is not None else None
    rules = _prefix_rules(data)
    explicit = _explicit_families(data, URIRef(artifact_iri))
    if explicit:
        return FamilyRecognition(tuple(sorted(explicit)), "explicit")

    candidates = {}
    values = (artifact_iri, path, graph_iri)
    for method, value in zip(PREFIX_METHODS, values):
        if value is None:
            continue
        matches = []
        for family, prefix in rules[method]:
            matches_prefix = (
                "/" + prefix in "/" + value
                if method == ARTGOV.filePathPrefix else value.startswith(prefix)
            )
            if matches_prefix:
                matches.append((family, prefix))
        if not matches:
            continue
        longest = max(len(prefix) for _, prefix in matches)
        best = {family for family, prefix in matches if len(prefix) == longest}
        if len(best) > 1:
            raise RecognitionError(f"Ambiguous {method.split('#')[-1]}: {', '.join(sorted(best))}")
        candidates[method] = best.pop()
    families = set(candidates.values())
    if len(families) > 1:
        evidence = ", ".join(f"{method.split('#')[-1]}={family}" for method, family in candidates.items())
        raise RecognitionError(f"Conflicting family recognition: {evidence}")
    return FamilyRecognition(tuple(sorted(families)), "recognized" if families else "unmatched")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="+", type=Path, help="Turtle registry and membership files")
    parser.add_argument("--artifact", required=True, help="Artifact IRI to recognize")
    parser.add_argument("--source-path", help="Actual source file path, independent of graph name")
    parser.add_argument("--graph-iri", help="Named-graph IRI, if available")
    args = parser.parse_args()
    data = Graph()
    for path in args.data:
        data.parse(path, format="turtle")
    try:
        result = recognize_family(data, args.artifact, source_path=args.source_path,
                                  graph_iri=args.graph_iri)
    except RecognitionError as error:
        parser.error(str(error))
    print(json.dumps({"families": [str(family) for family in result.families], "basis": result.basis}))


if __name__ == "__main__":
    main()
