# Agent instructions

These instructions apply throughout this repository. Read any more specific
directory instructions before changing files there.

## Working rules

- No compliments. Communicate plainly and report evidence and limitations.
- Find root causes. Do not substitute symptom fixes or workarounds.
- Breaking changes are welcome when they improve the model. Do not preserve
  incorrect axioms or add compatibility layers merely to avoid breaking changes.
- Fail fast on invalid data, ambiguous identities, unsupported behavior, and
  violated invariants. Do not silently skip data or invent fallback semantics.
- For a bug, write a regression test first, demonstrate its failure, then fix
  the implementation until the test passes.
- Treat architectural decision records as authoritative if present. Surface
  conflicts rather than silently disregarding them.
- Preserve unrelated working-tree changes. Other contributors may be editing
  this repository or sibling repositories concurrently.
- Do not commit, push, or publish externally unless requested.
- Do not modify sibling repositories without authorization.

## Repository orientation

Read [README.md](README.md) and the relevant documentation before model changes:

- [Ontology catalog and namespaces](docs/ontologies.md)
- [Governance and registered identities](docs/governance.md)
- [Families and recognition](docs/families.md)
- [Publication and approvals](docs/publication.md)
- [Lifecycles](docs/lifecycles.md)
- [Documentation coverage and modeling review](docs/documentation-audit.md)

Ontology sources are root-level `ekgf-*.ttl` files. Registry data lives in
`dataset/`, validation tests in `tests/`, and utilities in `scripts/`.

## Ontology and registry conventions

- Keep RDF in valid Turtle and preserve the distinction between ontology axioms,
  documentation annotations, registry data, and generated documentation.
- Use the declared namespace and preferred prefix. Maintain SHACL `sh:declare`,
  `sh:prefix`, and `sh:namespace` metadata when changing namespace declarations.
- Give locally defined named, explicitly typed resources English labels,
  meaningful definitions, and `rdfs:isDefinedBy` links to their source ontology.
  Keep ontology headers named, described, and licensed.
- Do not fabricate business meaning from a resource name. Identify unresolved
  modeling questions explicitly rather than presenting guesses as definitions.
- Documentation-only changes must not silently alter domains, ranges, imports,
  restrictions, class relationships, constraints, or registered identities.
  Treat intended semantic changes explicitly and test their consequences.
- Reuse registered UUID identities. Names, domains, and URLs are metadata, not
  substitutes for stable identity.
- Keep authority roles distinct from the organizations playing them. Preserve
  explicit role-to-player relationships.
- Families are optional. Do not make family membership a prerequisite for
  artifact governance or publication. Versions and approvals concern releases.
- Preserve the distinction between local term ownership and declarations of
  external vocabulary terms. Do not claim ownership of imported terms.
- Keep graph assertions, documentation, catalogs, and tests consistent.

## Verification

Use the dependencies in `requirements-test.txt` and run tests from this
repository's root:

```sh
python3 -B -m unittest discover -s tests -v
git diff --check
```

Run the relevant regression test first, then the complete suite for changes to
ontology semantics or shared registries. Keep tests reproducible and offline;
use the existing vocabulary fixtures rather than fetching imports implicitly.
Report what was checked and any remaining limitations. Passing annotation
coverage does not establish business accuracy or semantic correctness.

## Shell scripts

Never write `set -e`, `set -eu`, `set -euo pipefail`, or `set -o errexit`.
Check each command's exit status explicitly at its call site with `if`, an
explicit status variable, or a failure handler. Ignore a failure only when it is
genuinely harmless, with a comment explaining why. `set -u` and
`set -o pipefail` on their own are allowed.

The shell disables errexit in several conditional contexts, including functions
called from those contexts. It therefore cannot provide reliable error coverage.
