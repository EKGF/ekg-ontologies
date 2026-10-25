# Generate the ontology family reference

[Documentation index](../README.md#documentation)

[GraphArch](https://github.com/EKGF/grapharch) builds a standards-style HTML
reference and a matching PDF directly from this checkout's ontology files and
registry. The publication settings are in
[`publication/grapharch.ttl`](../publication/grapharch.ttl). They refer to the
existing EKGF family and authority UUIDs; they do not redefine those identities
or change ontology axioms. The generated reference is an editor's draft, not an
approved standards release.

## Build locally

Install a published GraphArch release, then run from this repository's root:

```sh
grapharch publication build-family \
  --local-repository . \
  --definitions publication/grapharch.ttl \
  --project urn:ekgf-ontologies:documentation:project \
  --target urn:ekgf-ontologies:documentation:specification \
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

The **Build ontology reference** workflow is manual while the first verified
GraphArch binary release is being published. Once that release is available,
run it from the Actions tab with its exact version, without a leading `v`.
The workflow uses the GraphArch action pinned to a full commit SHA, builds from
`actions/checkout`, and uploads the HTML, PDF and KG archive as workflow artifacts.
It does not publish a release or deploy GitHub Pages.

The action takes the same source, definitions, project, target and output settings
as the local command. It downloads and verifies the selected release binary;
it does not compile GraphArch or require a Rust installation in this repository.
After the first verified run, push/PR triggers or a separately authorized Pages
deployment can be added using the same publication configuration.

Update the publication date and version URLs in the Turtle configuration when
preparing a new publication. Authority labels, family members, descriptions and
ontology terms continue to come from their existing source files and registry.
