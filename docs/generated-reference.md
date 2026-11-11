# Generate the EKGF ontology family website

[Documentation index](../README.md#documentation)

[GraphArch v0.2.8](https://github.com/EKGF/grapharch/releases/tag/v0.2.8) builds
the EKGF website, a multipage ontology family reference and a PDF directly from
this checkout. The publication settings are in
[`publication/grapharch.ttl`](../publication/grapharch.ttl). They refer to the
existing EKGF family and authority UUIDs; they do not redefine those identities
or change ontology axioms. The generated reference is an editor's draft, not an
approved standards release.

This repository publishes from `main`. The family reference uses `spec/main/`
and the PDF edition uses `documents/main/`. The paginated family reference does
not produce a combined PDF, so the PDF edition is a separate publication target.
It renders the whole family as one document, `documents/main/document.pdf`,
with a single-page HTML rendition beside it. The `documents/<branch>` path
follows GraphArch's convention for a family's PDF edition.

The [website](https://ekgf.github.io/ekg-ontologies/) uses the shared EKGF header,
footer, typography and theme controls, as other EKGF websites do. Its authored
introduction and usage page live in [`publication/site/`](../publication/site/).
The site's primary navigation places **Ontology family** and **PDF** in the
second bar beside the site name. The top bar carries shared EKGF navigation.
These cross-publication links use their canonical URLs, as required by
GraphArch v0.2.8's primary navigation.

The [family reference](https://ekgf.github.io/ekg-ontologies/spec/main/)
uses the same `ga:SpecificationPagesRenderer` as GraphArch's Commons showcase:
a family overview, one reference page per ontology, links between terms, and
shared search. The registered family explicitly selects `ga:collectionTerm
"family"`. It retains its own name, EKGF publishing authority and namespaces.
The [PDF edition](https://ekgf.github.io/ekg-ontologies/documents/main/document.pdf)
contains the complete reference as a book. The reference's
[documentation graph](https://ekgf.github.io/ekg-ontologies/spec/main/documentation.nq)
is available as a restorable RDF archive.

## Build locally

Install the verified GraphArch **v0.2.8** release, then run from this repository's root:

```sh
python3 -B scripts/build_grapharch_pages.py
```

Use `--grapharch /path/to/grapharch` if the executable is not on `PATH`.
The command requires a fresh `_site/` directory and fails if one already exists.
Move or remove your previous generated `_site/` tree before rebuilding.

The script explicitly selects three targets from `publication/grapharch.ttl`:

| Target | Renderer | Generated destination |
| --- | --- | --- |
| `doc:website` | `ga:WebsiteRenderer`, EKGF theme and documentation layout | `_site/site/` |
| `doc:specification` | `ga:SpecificationPagesRenderer` | `_site/spec/main/` |
| `doc:pdf` | `ga:SpecificationRenderer`, including its PDF | `_site/documents/main/` |

Here `doc:` is `urn:ekgf-ontologies:documentation:`. The website has its own
scope and profile. The reference and book share the registered family profile.
The configuration records this arrangement in `annotation:markdownDescription`.

Each family target uses `publication build-family --local-repository .` with
explicit `--definitions`, `--project` and `--target` arguments. The source
checkout is read directly. Ontologies are not copied into another
repository, and imports are not downloaded. Git provenance records the observed
checkout state, including local edits. The website uses `publication build-site`
on `publication/site/` with its own explicit target.

The script checks each versioned JSON build report and retains that target's
`documentation.nq` beside its pages before the next target runs. It then uses
GraphArch's `publication package-site` with
[`publication/hosting.yaml`](../publication/hosting.yaml) to combine the three
artifact trees. Packaging rejects collisions, private files and symlinks.
Graph stores and intermediate build directories are excluded.

The deployable static tree is `_site/pages/.vercel/output/static/`. Its root is
the EKGF website; the family reference remains at `spec/main/`, and the book
is at `documents/main/`. Each has its own restorable `documentation.nq`.
Serve the assembled tree to preview the complete site:

```sh
python3 -m http.server 8770 --directory _site/pages/.vercel/output/static
```

`_site/` is ignored by Git
and excluded from source discovery, so generated RDF cannot become an input to
the next run. Do not commit generated output.

## Build in GitHub Actions

The **Publish ontology reference** workflow runs when ontology, registry,
documentation or publication sources change. Pull requests build and check the
reference; successful builds on `main` deploy it to GitHub Pages. You can also
run the workflow manually. The site root serves the EKGF website, and the
family reference retains its canonical `spec/main/` URL.

The workflow uses the GraphArch action pinned to a full commit SHA and a verified
binary release version. Both the action and the release's expected source
revision are pinned to `595e55913096cb7f39633189ef67f5d916ef4dcc`.
It builds directly from `actions/checkout`, running the same build script as
the local command. A failed renderer or invalid report stops packaging and deployment.
It downloads and verifies the release binary; no Rust installation or compilation
is required. Generated HTML, PDF and the restorable KG archive are included in
the Pages artifact. The workflow uploads only the assembled static tree.

Update the publication date and version URLs in the Turtle configuration when
preparing a new publication. Authority labels, family members, descriptions and
ontology terms continue to come from their existing source files and registry.
