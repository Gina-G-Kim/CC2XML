# CC2XML

Parses a standard-shaped Common Criteria Security Target / Protection
Profile document (plain text or markdown) into structured XML, following
the schema and parsing rules in `devnotes/` (see `devnotes/README.md`), and validates the result
against `cc_2022.xml` (the CC Portal's SFR/SAR catalog) plus internal
self-consistency checks.

> **`devnotes/` and `ref/` are not tracked by this repository** (see
> `.gitignore`) - they're local working material: `devnotes/` is a
> session-by-session dev journal recording *why* each schema/parsing
> decision below was made, and `ref/` holds the bulky ISO/IEC 15408
> standard PDFs, `cc_2022.xml`, and real sample ST PDFs
> (`ref/sample_sts/`) this project was built and verified against. Every
> `devnotes/...`/`ref/...` path referenced in this README assumes you have
> that directory locally; from a fresh clone without it, the reasoning
> those files document isn't available here - ask whoever maintains this
> project for a copy if you need it.

## Design basis (per devnotes/)

The design target is **ISO/IEC 15408-1/2/3:2022 and `cc_2022.xml` only** -
not any particular enterprise's ST authoring conventions. Earlier versions
of this project targeted real vendor-published ST/PP PDFs directly and
accumulated a large amount of code handling their house-style variance
(reversed/scrambled PDF table text, NIAP-style inherited-SFR restatement,
fallback element recovery, section-boundary richness scoring, etc.). All of
that has been removed: enterprise ST documents restyle the standard freely
and are not a reliable basis for a schema, and PDF extraction is no longer
part of this pipeline at all - input is authored directly as plain
text/markdown. Text outside the standard's structure is preserved verbatim
in `<unparsed_fragment>` rather than guessed at.

## Pipeline

```
tests/*.md|*.txt --[parser.py]--> XML tree
                                        |
                                [validate.py] --> <validation_report>
                                        |
                                  output/*.xml
```

- **`cc2xml/parser.py`** - the text parser. Builds the XML tree with a
  hand-written serializer (not `ET.tostring`) so `<raw>`/`<justification>`/
  etc. can be emitted as CDATA.
- **`cc2xml/catalog.py`** - loads `cc_2022.xml` into a lookup index. Its
  real tag names (`f-class`/`f-family`/`f-component`/`f-element`,
  `a-class`/`a-family`/`a-component`/`ae-developer`/`ae-content`/
  `ae-evaluator`) were confirmed by inspecting the actual file.
- **`cc2xml/validate.py`** - Stage 1 (vs. catalog) + Stage 2
  (self-consistency) checks, appended to the output as
  `<validation_report>`.
- **`cc2xml/cli.py`** - orchestrates the above. `python3 -m cc2xml.cli --all`
  processes every `.md`/`.txt` file in `tests/`.

## Schema simplifications vs. the enterprise-PDF-era design

The modification notes in `devnotes/` removed several fields that were enterprise
house-style artifacts rather than standard requirements:

- SPD: no `<assets>`/`<asset_refs>` blocks or per-threat `<rationale>` -
  ASE_SPD.1 doesn't define separate asset tagging; threat/agent/asset prose
  stays folded into `<description>`.
- Security Objectives: no `<application_note>`, no `OT.` id variant (only
  `O.`/`OE.`), no inline `spd_refs` - traceability lives only in the
  Rationale section.
- Conformance Claims: no `<allowed_with>` (PP-Configuration/ACE scope, not
  ST parsing) or `<conformance_rationale>`.
- Introduction: `<toe_reference>` merged into `<toe_overview>`
  (`toe_name`/`toe_version`/`toe_type`/`description`).
- SAR components: no `package_inherited`/`augmented` attributes - the
  parser reads what's actually in the text and doesn't guess EAL-package
  inheritance.
- Rationale: no X-matrix table-form parsing or `<rationale_table_raw>`
  fallback (ASE_OBJ.2/ASE_REQ.2 define rationale as narrative text; a table
  is a house convention) and no direct/derived branching (`rationale_type`
  is gone from the root element) - the shape is always the same, empty
  where nothing was found.

`dependency_rationale` is defined in the schema but - like
`sfr_rationale`/`objectives_rationale` before their own rules existed -
no note in `devnotes/` gives an extraction rule for it, so it's always empty.

## cc_2022.xml fallback for hierarchical_to/dependencies/elements

A real ST/PP often names a standard component ("FAU_GEN.1 Audit data
generation") without restating its hierarchical-to, dependencies, or element
text, because it's inherited unchanged from a base PP. Per
`devnotes/done/11-catalog-fallback.md`, `parser.apply_catalog_fallback` (invoked from
`parse_document` whenever a catalog is available) fills each of those three
fields from `cc_2022.xml` when the ST text left it empty - so a recognized
component's requirement name, hierarchy, dependencies, and description
(the element text) are unconditionally populated, never silently blank just
because the ST didn't restate them.

Each of `<hierarchical_to>`, `<dependencies>`, and `<elements>` carries a
`source` attribute: `"st"` if the ST text itself supplied it, `"catalog"` if
it was filled from the standard. Catalog-filled element text is the
standard's own generic, still-bracketed (`[assignment: ...]`/
`[selection: ...]`) wording - not a TOE-specific completed value - which is
exactly why the `source` attribute matters to a reader. This only applies to
non-extended components the catalog actually has an entry for; an extended
component (vendor-invented, not in the standard) or a component id the
catalog doesn't recognize is left as-is - the ST is the only possible source
for those.

## Testing

There is no corpus of real documents any more. Hand-written,
standard-shaped synthetic fixtures live in `tests/`:

- `tests/ideal_st.md` exercises every part of the schema (SPD, TOE/
  environment objectives, an extended component, SFRs with hierarchical-to/
  dependencies/operations, an EAL1 SAR package, objectives/SFR rationale,
  TOE Summary Specification) against real `cc_2022.xml` catalog entries,
  fully restated (no catalog fallback needed - `source="st"` throughout).
- `tests/catalog_fallback_probe.md` claims two SFRs and one SAR by name only,
  without restating hierarchical-to/dependencies/elements, to exercise the
  cc_2022.xml fallback above (`source="catalog"` on all three fields for
  those components).
- `tests/arbit_data_diode_st.md` adapts a real, published Security Target
  (a data-diode hardware TOE from `ref/sample_sts/1096V2b_pdf.pdf`) into the
  standard shape this parser expects, keeping its actual requirement wording
  (threats/assumptions/objectives/SFR operation text/rationale prose) rather
  than hand-written prose - real natural-language phrasing, restructured
  only where the source used a non-standard convention (e.g. table-form
  rationale rewritten as bare-id-then-paragraph, `T.DATA LEAK` -> `T.DATA_LEAK`
  to fit the id grammar). It also mixes fully-restated and name-only
  components deliberately, exercising the cc_2022.xml fallback on
  realistic content instead of a minimal synthetic probe.

```
python3 -m cc2xml.cli tests/ideal_st.md
# or: python3 -m cc2xml.cli --all
```

All three currently parse and validate clean (`PASS`, zero issues, Stage 1
and Stage 2 both run). When extending the schema or parsing rules, extend
these fixtures (or add another one alongside them in `tests/`) to cover the
new shape, rather than reasoning about a real-world PDF corpus.

**`tests/test_parser.py`** is a `unittest`-based suite (stdlib only, no
pytest) targeting individual functions (`parse_dependencies`,
`find_component_blocks`, `apply_catalog_fallback`,
`validate._satisfies_dependency`, etc.) rather than whole documents. Several
cases are pinned directly to real bugs found while building this project
(`devnotes/done/12`, `/14`, `/15`, `/16`) - they catch the exact regression
in milliseconds instead of needing a full document's XML read by hand.
Two cases also pin *known, deliberate* current limitations (documented in
`devnotes/`) so a future change to that area is a conscious decision:

```
python3 -m unittest tests.test_parser -v
```

Whole-document fixtures and function-level unit tests catch different
things: a fixture answers "does a complete document parse into something
sensible," a unit test answers "does this function produce exactly this
output for this input." Both matter here - most bugs found so far were
only caught by reading a whole fixture's XML output closely, which is
exactly what the corresponding unit test now does automatically.

`output/*.xml` is committed, so after any parser change, `python3 -m
cc2xml.cli --all` followed by `git diff output/` is a free golden-file
regression check on top of the above - it shows precisely what changed
about every fixture's output, not just whether it still says `PASS`.

`ref/sample_sts/` holds 19 real, published enterprise ST PDFs (kept as
reference/example material only - nothing in `cc2xml/` reads PDFs any
more, see above). `output/` holds only the XML this pipeline currently
produces (`tests/*.md` + `templates/*.md`, regenerated by
`python3 -m cc2xml.cli --all`).

## Preparing real ST/PP content

`templates/ST_TEMPLATE.md` is a single reference document exercising every
text pattern the parser recognizes (catalog-fallback name-only components,
fully-restated components, AND/OR/unsatisfied dependencies, iteration,
selection-based/optional/objective inclusion, PP and EAL/package claims,
etc.), verified to parse `PASS` with zero issues. `templates/GUIDE.md`
explains each pattern block-by-block and how the same two SFR/SAR patterns
(name-only vs. fully-restated) scale to any EAL level or PP. Use these when
turning a real ST/PP into the plain-text/markdown shape this parser expects.

## Running

No external dependencies - `python3 -m cc2xml.cli` uses only the stdlib.

```
python3 -m cc2xml.cli tests/ideal_st.md     # a single file
python3 -m cc2xml.cli --all                  # every .md/.txt file in tests/
python3 -m cc2xml.cli --all --no-catalog     # skip Stage-1 cc_2022.xml validation
```

Or via `./cc2xml_run` at the repo root, an executable that just wraps
`cc2xml.cli.main()` (same arguments as above). Its exit code is `0` only
if every processed file's result was `PASS`/`WARN`, `1` if any was `FAIL`
or hit an `ERROR` - so it's usable directly as a CI/script gate.
