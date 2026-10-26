# Generate the ontology family reference

[Documentation index](../README.md#documentation)

[GraphArch](https://github.com/EKGF/grapharch) builds a standards-style HTML
reference and a matching PDF directly from this checkout's ontology files and
registry. The publication settings are in
[`publication/grapharch.ttl`](../publication/grapharch.ttl). They refer to the
existing EKGF family and authority UUIDs; they do not redefine those identities
or change ontology axioms. The generated reference is an editor's draft, not an
approved standards release.

Read the generated [EKGF ontology reference](https://ekgf.github.io/ekg-ontologies/spec/develop/).
Its PDF download contains the same specification, and its
[documentation graph](https://ekgf.github.io/ekg-ontologies/spec/develop/documentation.nq)
is available as a restorable RDF archive.

## Build locally

Install a published GraphArch release, then run from this repository's root:

```sh
grapharch publication build-family \
  --local-repository . \
  --output-root _site \
  --json
```

The source checkout is read directly. Ontologies are not copied into another
repository, and imports are not downloaded. Git provenance records the observed
checkout state, including local edits. Edit a source file and run the same command
again to regenerate the reference.

The JSON result reports the actual `publication_path`, `pdf_path`, and `kg_path`,
plus the pinned plan and snapshot. The HTML and PDF are under
`_site/spec/develop/`; the complete restorable KG archive is
`_site/documentation.nq`. Logs go to standard error. `_site/` is ignored by Git
and excluded from source discovery, so generated RDF cannot become an input to
the next run. Do not commit generated output.

## Build in GitHub Actions

The **Publish ontology reference** workflow runs when ontology, registry,
documentation or publication sources change. Pull requests build and check the
reference; successful builds on `main` deploy it to GitHub Pages. You can also
run the workflow manually. The site root redirects to `spec/develop/`, preserving
the canonical version URLs declared in the publication settings.

The workflow uses the GraphArch action pinned to a full commit SHA and a verified
binary release version. It builds directly from `actions/checkout`, discovering
the project and target from `publication/grapharch.ttl`, as the local command does.
It downloads and verifies the release binary; no Rust installation or compilation
is required. Generated HTML, PDF and the restorable KG archive are included in
the Pages artifact. The persistent graph store is not published.

Update the publication date and version URLs in the Turtle configuration when
preparing a new publication. Authority labels, family members, descriptions and
ontology terms continue to come from their existing source files and registry.
