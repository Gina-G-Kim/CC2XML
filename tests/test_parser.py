"""
Unit tests for cc2xml/parser.py and cc2xml/validate.py's individual
functions - complements the whole-document `.md` fixtures in this same
directory (tests/*.md, run via `python3 -m cc2xml.cli --all`).

The fixtures answer "does a whole document parse into something sensible";
these answer "does this specific function produce exactly this output for
this input" - most of the bugs found while building this project
(devnotes/done/12, /15, /16) were only caught by manually reading a whole
document's XML output. A unit test pinned to the exact input that triggered
each one catches it in milliseconds instead.

Run with:
    python3 -m unittest tests.test_parser -v
    (from the repository root, so `cc2xml` is importable)
"""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from cc2xml import parser, validate, catalog

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'ref' / 'cc_2022.xml'


class TestParseDependencies(unittest.TestCase):
    """R7 (parser.parse_dependencies) - devnotes/done/12, /15, /16."""

    def _deps(self, dep_text_lines):
        lines = ['Dependencies: ' + dep_text_lines[0]] + list(dep_text_lines[1:])
        return parser.parse_dependencies(lines, 0, len(lines))

    def test_no_dependencies(self):
        self.assertEqual(self._deps(['No dependencies.']), [])

    def test_single_dependency(self):
        self.assertEqual(self._deps(['FIA_UID.1']),
                          [{'alternatives': ['FIA_UID.1'], 'unsatisfied': False}])

    def test_comma_list_is_and_not_or(self):
        """devnotes/done/12: 'A, B, C' means all three required, not one-of."""
        deps = self._deps(['FDP_ACC.1, FMT_SMR.1, FMT_SMF.1'])
        self.assertEqual(deps, [
            {'alternatives': ['FDP_ACC.1'], 'unsatisfied': False},
            {'alternatives': ['FMT_SMR.1'], 'unsatisfied': False},
            {'alternatives': ['FMT_SMF.1'], 'unsatisfied': False},
        ])

    def test_bracket_or_group(self):
        deps = self._deps(['[FDP_ACC.1 or FDP_IFC.1]'])
        self.assertEqual(len(deps), 1)
        self.assertEqual(sorted(deps[0]['alternatives']), ['FDP_ACC.1', 'FDP_IFC.1'])
        self.assertFalse(deps[0]['unsatisfied'])

    def test_plain_or_without_brackets(self):
        deps = self._deps(['FIA_UID.1 or FIA_UID.2'])
        self.assertEqual(len(deps), 1)
        self.assertEqual(sorted(deps[0]['alternatives']), ['FIA_UID.1', 'FIA_UID.2'])

    def test_bare_id_on_its_own_line_is_a_separate_and_dependency(self):
        """devnotes/done/16: a lone id with nothing else on its own line must
        not be swallowed as a boundary - it's one more AND-required dep."""
        deps = self._deps(['FDP_ACC.1', 'FMT_MSA.3'])
        self.assertEqual(deps, [
            {'alternatives': ['FDP_ACC.1'], 'unsatisfied': False},
            {'alternatives': ['FMT_MSA.3'], 'unsatisfied': False},
        ])

    def test_bracket_or_group_plus_bare_and_line(self):
        """devnotes/done/16's exact reproduction (FCS_COP.1's dependencies)."""
        deps = self._deps(['[FCS_CKM.1 or FCS_CKM.5]', 'FCS_CKM.3'])
        self.assertEqual(len(deps), 2)
        self.assertEqual(sorted(deps[0]['alternatives']), ['FCS_CKM.1', 'FCS_CKM.5'])
        self.assertEqual(deps[1], {'alternatives': ['FCS_CKM.3'], 'unsatisfied': False})

    def test_unsatisfied_justification_on_its_own_line(self):
        """devnotes/done/15's exact reproduction (the real Arbit ST wording)."""
        deps = self._deps([
            'FDP_IFC.1',
            'FMT_MSA.3 not resolved. The TOE configuration is static and has',
            'therefore no concept of manageable security attributes.',
        ])
        self.assertEqual(len(deps), 2)
        satisfied = [d for d in deps if not d['unsatisfied']]
        unsatisfied = [d for d in deps if d['unsatisfied']]
        self.assertEqual(satisfied, [{'alternatives': ['FDP_IFC.1'], 'unsatisfied': False}])
        self.assertEqual(len(unsatisfied), 1)
        self.assertEqual(unsatisfied[0]['alternatives'], ['FMT_MSA.3'])
        self.assertIn('not resolved', unsatisfied[0]['justification'])
        self.assertIn('manageable security attributes', unsatisfied[0]['justification'])

    def test_known_limitation_same_line_justification_not_recognized(self):
        """devnotes/done/15's documented residual limitation: a justification
        crammed onto the *same* line as the dependency list is NOT
        recognized (falls through as an ordinary satisfied dependency). This
        test pins the *current* behavior down deliberately, so a future
        change to this area is a conscious decision, not an accident."""
        deps = self._deps(['FDP_IFC.1, FMT_MSA.3 (not applicable - static configuration)'])
        self.assertTrue(all(not d['unsatisfied'] for d in deps),
                         'if this now fails, the known limitation in '
                         'devnotes/done/15 may have been fixed - update that '
                         'note and this test together')


class TestComponentBoundaryDetection(unittest.TestCase):
    """find_component_blocks / _next_marker_index - devnotes/done/15, /16:
    a line starting with a valid CC id must only be treated as a new
    component/field boundary when it actually looks like one (has a real
    name, and isn't a dependency-unsatisfied justification)."""

    def test_bare_id_line_does_not_split_the_surrounding_component(self):
        lines = [
            'FCS_COP.1/Hash Cryptographic operation',
            '',
            'Dependencies: [FCS_CKM.1 or FCS_CKM.5]',
            'FCS_CKM.3',
            '',
            'FCS_COP.1.1/Hash The TSF shall perform hashing.',
        ]
        blocks = parser.find_component_blocks(lines)
        self.assertEqual(len(blocks), 1, 'the bare FCS_CKM.3 line must not '
                          'start a second (phantom) component block')
        start, end, m = blocks[0]
        self.assertEqual(end, len(lines), 'the real component\'s block must '
                          'extend to include its own element line')

    def test_unsatisfied_justification_does_not_split_the_component(self):
        lines = [
            'FDP_IFF.1 Simple security attributes',
            '',
            'Dependencies: FDP_IFC.1',
            'FMT_MSA.3 not resolved. Not applicable to this TOE.',
            '',
            'FDP_IFF.1.1 The TSF shall enforce the [assignment: SFP].',
        ]
        blocks = parser.find_component_blocks(lines)
        self.assertEqual(len(blocks), 1)
        start, end, m = blocks[0]
        self.assertEqual(end, len(lines))

    def test_real_second_component_still_splits_correctly(self):
        """Guards against over-correcting: a genuine second component (id +
        real name) must still start a new block."""
        lines = [
            'FDP_ACC.1 Subset access control',
            '',
            'FDP_ACF.1 Security attribute based access control',
            '',
        ]
        blocks = parser.find_component_blocks(lines)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][1], 2)  # first block ends where the 2nd starts


class TestParseHierarchicalTo(unittest.TestCase):

    def test_no_other_components(self):
        lines = ['Hierarchical to: No other components.']
        self.assertEqual(parser.parse_hierarchical_to(lines, 0, 1), [])

    def test_single_hierarchical_component(self):
        lines = ['Hierarchical to: FIA_UAU.1']
        self.assertEqual(parser.parse_hierarchical_to(lines, 0, 1), ['FIA_UAU.1'])


class TestParseOperations(unittest.TestCase):

    def test_assignment(self):
        ops = parser.parse_operations('The TSF shall do [assignment: something].')
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]['type'], 'assignment')
        self.assertEqual(ops[0]['label'], '(a1)')

    def test_selection_options_split_on_comma(self):
        ops = parser.parse_operations('[selection: minimum, basic, detailed]')
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]['type'], 'selection')
        self.assertEqual(ops[0]['options'], ['minimum', 'basic', 'detailed'])

    def test_selection_options_split_on_either_comma_or_semicolon(self):
        """`,` and `;` are both always treated as option separators (not
        "prefer ; when present, to preserve internal commas") - a document
        using ';' because an option's own text contains a comma still gets
        that comma split too. Documented as-is in parser.py; pinning current
        behavior here rather than the smarter split one might expect."""
        ops = parser.parse_operations('[selection: RFC 4251, 4252; RFC 4253, 4254]')
        self.assertEqual(ops[0]['options'], ['RFC 4251', '4252', 'RFC 4253', '4254'])

    def test_nested_assignment_inside_selection(self):
        ops = parser.parse_operations(
            '[selection: fixed value, [assignment: other value]]')
        types = sorted(op['type'] for op in ops)
        self.assertEqual(types, ['assignment', 'selection'])
        nested = [op for op in ops if op['type'] == 'assignment'][0]
        self.assertEqual(nested['nested_in'], '(s1)')


class TestDetectInclusion(unittest.TestCase):

    def test_default_is_mandatory(self):
        self.assertEqual(parser.detect_inclusion('Just a normal SFR.'), 'mandatory')

    def test_selection_based(self):
        self.assertEqual(
            parser.detect_inclusion('This SFR is selection-based on FTP_ITC.1.'),
            'selection_based')

    def test_optional(self):
        self.assertEqual(
            parser.detect_inclusion('This is an optional SFR for this TOE.'),
            'optional')

    def test_objective(self):
        self.assertEqual(
            parser.detect_inclusion('This is an objective SFR, not mandatory.'),
            'objective')

    def test_optional_reversed_word_order(self):
        """devnotes/done/17: "SFR is optional" (not "optional SFR") must
        also be recognized - this exact phrasing is what
        templates/ST_TEMPLATE.md's FAU_SAR.1 example uses."""
        self.assertEqual(
            parser.detect_inclusion('This SFR is optional, included only when supported.'),
            'optional')

    def test_objective_reversed_word_order(self):
        self.assertEqual(
            parser.detect_inclusion('This SFR is an objective SFR representing best practice.'),
            'objective')


@unittest.skipUnless(CATALOG_PATH.exists(), f'{CATALOG_PATH} not present')
class TestCatalogFallback(unittest.TestCase):
    """apply_catalog_fallback / parse_document(catalog=...) -
    devnotes/done/11: hierarchical_to/dependencies/elements must always be
    populated for a recognized non-extended component."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.load_catalog(str(CATALOG_PATH))

    def _parse(self, sfr_body):
        text = (
            "Test Doc\nVersion 1.0\n2026-01-01\n\n"
            "1. Introduction\nTest.\n\n"
            "2. Conformance Claims\nCC:2022 Part 2 conformant, Part 3 conformant, EAL1.\n\n"
            "3. Security Problem Definition\nT.X\nTest threat.\n\n"
            "4.1 Security Objectives for the TOE\nO.X\nTest objective.\n\n"
            "4.2 Security Objectives for the Operational Environment\nOE.X\nTest.\n\n"
            "5. Extended Components Definition\nNone.\n\n"
            "6. Security Functional Requirements\n\n" + sfr_body + "\n\n"
            "8. Security Requirements Rationale\nO.X\nAddresses T.X.\n\n"
            "9. TOE Summary Specification\nTest.\n"
        )
        root, _ = parser.parse_document(text, catalog=self.catalog)
        return root

    def test_name_only_component_gets_full_catalog_fallback(self):
        root = self._parse("FAU_GEN.1 Audit data generation\n\nInherited unchanged.\n")
        comp = root.find('.//sfrs//component')
        self.assertEqual(comp.get('id'), 'FAU_GEN.1')
        hier = comp.find('hierarchical_to')
        deps = comp.find('dependencies')
        elements = comp.find('elements')
        self.assertEqual(hier.get('source'), 'catalog')
        self.assertEqual(deps.get('source'), 'catalog')
        self.assertEqual(elements.get('source'), 'catalog')
        self.assertGreater(len(elements), 0, 'catalog fallback must never '
                            'leave <elements/> empty for a real catalog id')
        # FAU_GEN.1 depends on FPT_STM.1 per cc_2022.xml
        dep_ids = {c.get('id') for d in deps.findall('dependency')
                   for c in d.find('alternatives')}
        self.assertIn('FPT_STM.1', dep_ids)

    def test_st_supplied_values_are_never_overridden(self):
        # FIA_UAU.2 really is hierarchical to FIA_UAU.1 and really does
        # depend on FIA_UID.1 per cc_2022.xml - restating them explicitly
        # (matching the catalog) is what "the ST supplied real content"
        # looks like; fallback must leave them exactly as written, not
        # duplicate or re-derive them.
        root = self._parse(
            "FIA_UAU.2 User authentication before any action\n\n"
            "Hierarchical to: FIA_UAU.1\n"
            "Dependencies: FIA_UID.1\n\n"
            "FIA_UAU.2.1 The TSF shall require each user to be successfully\n"
            "authenticated before allowing any other TSF-mediated action.\n"
        )
        comp = root.find('.//sfrs//component')
        hier = comp.find('hierarchical_to')
        deps = comp.find('dependencies')
        elements = comp.find('elements')
        self.assertEqual(hier.get('source'), 'st')
        self.assertEqual(deps.get('source'), 'st')
        self.assertEqual(elements.get('source'), 'st')
        self.assertEqual([c.get('id') for c in hier], ['FIA_UAU.1'])
        self.assertEqual(len(deps), 1)

    def test_explicit_empty_claim_is_indistinguishable_from_silence(self):
        """Known limitation: an ST that explicitly (and here, incorrectly)
        writes "Hierarchical to: No other components." for a component that
        actually has a real catalog hierarchy cannot be told apart from an
        ST that simply never mentioned Hierarchical-to at all - both parse
        to an empty list, so catalog fallback fires either way and silently
        fills in the real value with source="catalog" rather than flagging
        the ST's explicit (wrong) claim. Pinned deliberately: if this ever
        changes (e.g. a rule is added to preserve/flag an explicit "No
        other components." claim), update this test too."""
        root = self._parse(
            "FIA_UAU.2 User authentication before any action\n\n"
            "Hierarchical to: No other components.\n"
            "Dependencies: FIA_UID.1\n\n"
            "FIA_UAU.2.1 The TSF shall require each user to be successfully\n"
            "authenticated before allowing any other TSF-mediated action.\n"
        )
        comp = root.find('.//sfrs//component')
        hier = comp.find('hierarchical_to')
        self.assertEqual(hier.get('source'), 'catalog')
        self.assertEqual([c.get('id') for c in hier], ['FIA_UAU.1'])


@unittest.skipUnless(CATALOG_PATH.exists(), f'{CATALOG_PATH} not present')
class TestSatisfiesDependencyHierarchicalSubstitution(unittest.TestCase):
    """validate._satisfies_dependency - devnotes/done/14."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.load_catalog(str(CATALOG_PATH))

    def test_direct_match(self):
        self.assertTrue(validate._satisfies_dependency(
            self.catalog, 'FDP_IFC.1', {'FDP_IFC.1'}))

    def test_hierarchically_superior_component_satisfies_it(self):
        # FDP_IFC.2 is hierarchical to FDP_IFC.1 per cc_2022.xml.
        self.assertTrue(validate._satisfies_dependency(
            self.catalog, 'FDP_IFC.2', {'FDP_IFC.1'}))

    def test_unrelated_component_does_not_satisfy_it(self):
        self.assertFalse(validate._satisfies_dependency(
            self.catalog, 'FAU_GEN.1', {'FDP_IFC.1'}))

    def test_end_to_end_no_false_dependency_mismatch(self):
        """The exact devnotes/done/14 reproduction, through the real
        validator, not just the helper function in isolation."""
        text = (
            "Test Doc\nVersion 1.0\n2026-01-01\n\n"
            "1. Introduction\nTest.\n\n"
            "2. Conformance Claims\nCC:2022 Part 2 conformant, Part 3 conformant, EAL1.\n\n"
            "3. Security Problem Definition\nT.X\nTest threat.\n\n"
            "4.1 Security Objectives for the TOE\nO.X\nTest.\n\n"
            "4.2 Security Objectives for the Operational Environment\nOE.X\nTest.\n\n"
            "5. Extended Components Definition\nNone.\n\n"
            "6. Security Functional Requirements\n\n"
            "FDP_IFC.2 Complete information flow control\n\n"
            "FDP_IFC.2.1 The TSF shall enforce [assignment: SFP] on [assignment: subjects].\n"
            "FDP_IFC.2.2 The TSF shall ensure all operations are covered.\n\n"
            "FDP_IFF.1 Simple security attributes\n\n"
            "Dependencies: FDP_IFC.2\n\n"
            "FDP_IFF.1.1 The TSF shall enforce [assignment: SFP] based on [assignment: attrs].\n\n"
            "8. Security Requirements Rationale\nO.X\nAddresses T.X.\n\n"
            "9. TOE Summary Specification\nTest.\n"
        )
        root, _ = parser.parse_document(text, catalog=self.catalog)
        report = validate.validate(root, catalog=self.catalog)
        issue_types = {i.get('type') for i in report.find('issues')}
        self.assertNotIn('DEPENDENCY_MISMATCH', issue_types)


class TestFindSectionSpans(unittest.TestCase):
    """R2 (parser.find_section_spans) - simple first-match-in-canonical-order
    search (the richness-scoring machinery from the abandoned real-PDF era
    is gone; a standard-shaped doc has each chapter title exactly once)."""

    def test_canonical_order_and_missing_section_omitted(self):
        lines = [
            '1. Introduction',
            'intro text',
            '2. Conformance Claims',
            'conformance text',
            '3. Security Problem Definition',
            'spd text',
            '6. Security Functional Requirements',
            'sfr text',
        ]
        spans = parser.find_section_spans(lines)
        self.assertEqual(set(spans), {'introduction', 'conformance_claims', 'spd', 'sfrs'})
        self.assertEqual(spans['introduction'], (0, 2))
        self.assertEqual(spans['conformance_claims'], (2, 4))
        self.assertEqual(spans['spd'], (4, 6))
        self.assertEqual(spans['sfrs'], (6, 8))
        self.assertNotIn('sars', spans, 'a section never mentioned must be '
                          'omitted, not given a bogus empty span')

    def test_relaxed_pass_finds_an_unnumbered_heading(self):
        lines = [
            'Security Problem Definition',  # no leading "3." - not HEADER_NUM_RE
            'T.X',
            'a threat',
        ]
        spans = parser.find_section_spans(lines)
        self.assertEqual(spans['spd'], (0, 3))


class TestParseSPD(unittest.TestCase):

    def test_categorizes_by_prefix_and_captures_multiline_description(self):
        text = (
            'T.THREAT\n'
            'Line one of the threat.\n'
            'Line two of the threat.\n'
            'A.ASSUMPTION\n'
            'The assumption text.\n'
            'P.POLICY\n'
            'The policy text.\n'
        )
        data = parser.parse_spd(text)
        self.assertEqual(len(data['threats']), 1)
        self.assertEqual(data['threats'][0]['id'], 'T.THREAT')
        self.assertIn('Line one', data['threats'][0]['description'])
        self.assertIn('Line two', data['threats'][0]['description'])
        self.assertEqual(data['assumptions'][0]['id'], 'A.ASSUMPTION')
        self.assertEqual(data['osps'][0]['id'], 'P.POLICY')

    def test_osp_dot_prefix_also_categorized_as_osp(self):
        data = parser.parse_spd('OSP.EXAMPLE\nAn organizational security policy.\n')
        self.assertEqual(len(data['osps']), 1)
        self.assertEqual(data['osps'][0]['id'], 'OSP.EXAMPLE')


class TestParseObjectives(unittest.TestCase):

    def test_toe_and_env_ids_both_recognized(self):
        text = 'O.TOE\nTOE objective text.\nOE.ENV\nEnvironment objective text.\n'
        objs = parser.parse_objectives(text)
        ids = [o['id'] for o in objs]
        self.assertEqual(ids, ['O.TOE', 'OE.ENV'])

    def test_ot_variant_is_not_recognized(self):
        """devnotes/done/08: the OT. id variant was deliberately removed -
        an "OT.X" line must not be picked up as an objective at all."""
        objs = parser.parse_objectives('OT.LEGACY\nSome text that looks like an objective.\n')
        self.assertEqual(objs, [])


class TestParseRationale(unittest.TestCase):

    def test_objective_and_sfr_mappings_with_refs_extracted(self):
        text = (
            'O.EXAMPLE\n'
            'This objective addresses T.THREAT and A.ASSUMPTION.\n'
            'FIA_UID.2\n'
            'This component satisfies O.EXAMPLE.\n'
        )
        data = parser.parse_rationale(text)
        self.assertEqual(len(data['objectives_rationale']), 1)
        obj_map = data['objectives_rationale'][0]
        self.assertEqual(obj_map['objective_id'], 'O.EXAMPLE')
        self.assertEqual(obj_map['spd_refs'], ['A.ASSUMPTION', 'T.THREAT'])
        self.assertEqual(len(data['sfr_rationale']), 1)
        sfr_map = data['sfr_rationale'][0]
        self.assertEqual(sfr_map['comp_id'], 'FIA_UID.2')
        self.assertEqual(sfr_map['obj_refs'], ['O.EXAMPLE'])

    def test_iterated_component_id_is_kept_with_its_iteration_suffix(self):
        data = parser.parse_rationale('FCS_COP.1/Hash\nSatisfies O.X.\n')
        self.assertEqual(data['sfr_rationale'][0]['comp_id'], 'FCS_COP.1/Hash')


class TestBuildConformanceXml(unittest.TestCase):

    def test_part2_extended_part3_strict(self):
        el = parser.build_conformance_xml(
            'Part 2 extended and Part 3 conformant.', 'CC:2022')
        cc = el.find('cc_conformance')
        self.assertEqual(cc.find('part2_conformance').text, 'extended')
        self.assertEqual(cc.find('part3_conformance').text, 'strict')

    def test_pp_claim_requires_pp_prefixed_token(self):
        el = parser.build_conformance_xml(
            'Conformant to the Example Base Protection Profile.', 'CC:2022')
        self.assertEqual(len(el.find('pp_claims')), 0,
                          'prose alone must not be picked up as a PP claim')
        el2 = parser.build_conformance_xml('Conformant to PP-Example-Base.', 'CC:2022')
        self.assertEqual(el2.find('pp_claims')[0].get('ref'), 'PP-Example-Base')

    def test_eal_augmented_requires_no_comma_before_augmented(self):
        """Known quirk (templates/GUIDE.md): EAL_RE requires "augmented"
        immediately after the number - a comma in between defeats it."""
        with_comma = parser.build_conformance_xml(
            'Claims EAL2, augmented by ALC_FLR.2.', 'CC:2022')
        without_comma = parser.build_conformance_xml(
            'Claims EAL2 augmented by ALC_FLR.2.', 'CC:2022')
        self.assertEqual(with_comma.find('package_claims')[0].get('augmented'), 'false')
        self.assertEqual(without_comma.find('package_claims')[0].get('augmented'), 'true')


class TestParseDocReference(unittest.TestCase):

    def test_title_version_date_extracted(self):
        cover = 'Example Security Target\nVersion 1.0\n2026-01-01\n\n1. Introduction\n'
        ref = parser.parse_doc_reference(cover)
        self.assertEqual(ref['title'], 'Example Security Target')
        self.assertEqual(ref['version'], '1.0')
        self.assertEqual(ref['date'], '2026-01-01')

    def test_identifier_author_sponsor_are_always_blank(self):
        ref = parser.parse_doc_reference('Example ST\nVersion 1.0\n2026-01-01\n')
        self.assertEqual(ref['identifier'], '')
        self.assertEqual(ref['author'], '')
        self.assertEqual(ref['sponsor'], '')

    def test_known_quirk_sponsor_line_pollutes_title(self):
        """templates/GUIDE.md warns against writing a "Sponsor:"/"Developer:"
        cover-page line for exactly this reason - pinning the current
        (undesirable but real) behavior so a future accidental fix is
        noticed and the guide can be updated to match."""
        cover = 'Example ST\nVersion 1.0\n2026-01-01\nSponsor: Example Co.\n\n1. Introduction\n'
        ref = parser.parse_doc_reference(cover)
        self.assertIn('Sponsor: Example Co.', ref['title'],
                       'if this no longer happens, the cover-page guidance '
                       'in templates/GUIDE.md can be relaxed')

    def test_stops_at_first_numbered_heading(self):
        cover = 'Title Only\n1. Introduction\nThis must not leak into the title.\n'
        ref = parser.parse_doc_reference(cover)
        self.assertEqual(ref['title'], 'Title Only')


class TestSerialization(unittest.TestCase):
    """serialize()/_serialize_el() - output must always be well-formed XML,
    even with special characters or a literal "]]>" in CDATA-tagged text."""

    def test_special_characters_in_attributes_and_text_round_trip(self):
        root = parser.E('cc_document', title='A & B <C> "D"')
        root.append(parser.E('description', 'Text with <angle> & "quotes".'))
        xml_str = parser.serialize(root)
        parsed = ET.fromstring(xml_str)  # raises if malformed
        self.assertEqual(parsed.get('title'), 'A & B <C> "D"')
        self.assertEqual(parsed.find('description').text, 'Text with <angle> & "quotes".')

    def test_cdata_tag_survives_a_literal_close_marker(self):
        root = parser.E('raw', 'text containing ]]> a close marker')
        xml_str = parser.serialize(root)
        parsed = ET.fromstring(xml_str)
        self.assertEqual(parsed.text, 'text containing ]]> a close marker')

    def test_empty_element_serializes_as_self_closing(self):
        root = parser.E('dependencies')
        xml_str = parser.serialize(root)
        self.assertIn('<dependencies/>', xml_str)
        ET.fromstring(xml_str)


@unittest.skipUnless(CATALOG_PATH.exists(), f'{CATALOG_PATH} not present')
class TestStage2Validation(unittest.TestCase):
    """validate._stage2 - self-consistency checks that don't need the
    catalog, but sharing the same base-document builder as the catalog
    tests above is easiest via parse_document with no catalog fallback
    surprises (catalog=None -> Stage 1 skipped, only Stage 2 runs)."""

    def _base(self, spd='T.X\nA threat.\n', objectives_toe='O.X\nAn objective.\n',
              sfrs='FIA_UID.2 User identification before any action\n',
              rationale='O.X\nAddresses T.X.\n\nOE.X\nAddresses T.X.\n\nFIA_UID.2\nSatisfies O.X.\n'):
        text = (
            "Test Doc\nVersion 1.0\n2026-01-01\n\n"
            "1. Introduction\nTest.\n\n"
            "2. Conformance Claims\nCC:2022 Part 2 conformant, Part 3 conformant, EAL1.\n\n"
            f"3. Security Problem Definition\n{spd}\n\n"
            f"4.1 Security Objectives for the TOE\n{objectives_toe}\n\n"
            "4.2 Security Objectives for the Operational Environment\nOE.X\nTest.\n\n"
            "5. Extended Components Definition\nNone.\n\n"
            f"6. Security Functional Requirements\n\n{sfrs}\n\n"
            f"8. Security Requirements Rationale\n{rationale}\n\n"
            "9. TOE Summary Specification\nTest.\n"
        )
        root, _ = parser.parse_document(text, catalog=None)
        report = validate.validate(root, catalog=None)
        return {i.get('type') for i in report.find('issues')}

    def test_empty_spd_flagged(self):
        issue_types = self._base(spd='')
        self.assertIn('EMPTY_SPD', issue_types)

    def test_unmapped_objective_and_sfr_flagged(self):
        issue_types = self._base(rationale='')
        self.assertIn('UNMAPPED_OBJECTIVE', issue_types)
        self.assertIn('UNMAPPED_SFR', issue_types)

    def test_fully_covered_document_has_no_unmapped_warnings(self):
        issue_types = self._base()
        self.assertNotIn('UNMAPPED_OBJECTIVE', issue_types)
        self.assertNotIn('UNMAPPED_SFR', issue_types)

    def test_dangling_spd_ref_flagged(self):
        issue_types = self._base(
            rationale='O.X\nAddresses T.NONEXISTENT.\n\nFIA_UID.2\nSatisfies O.X.\n')
        self.assertIn('DANGLING_SPD_REF', issue_types)

    def test_malformed_operation_selection_with_no_options(self):
        # A selection bracket that resolves to zero usable options.
        issue_types = self._base(
            sfrs='FIA_UID.2 User identification before any action\n\n'
                 'FIA_UID.2.1 The TSF shall do [selection: ].\n')
        self.assertIn('MALFORMED_OPERATION', issue_types)


class TestDetectHelpers(unittest.TestCase):

    def test_doc_type_st_vs_pp(self):
        self.assertEqual(parser.detect_doc_type('This Security Target ...'), 'ST')
        self.assertEqual(parser.detect_doc_type(
            'This Protection Profile ... Protection Profile again ...'), 'PP')

    def test_eal_most_common_wins(self):
        text = 'EAL2 EAL2 EAL4'
        self.assertEqual(parser.detect_eal(text), 'EAL2')

    def test_eal_unknown_when_absent(self):
        self.assertEqual(parser.detect_eal('no assurance level mentioned'), 'unknown')

    def test_cc_version_2022(self):
        self.assertEqual(parser.detect_cc_version('Conformant to CC:2022.'), 'CC:2022')


class TestStage1ValidationDirect(unittest.TestCase):
    """validate._stage1, exercised directly against hand-built trees + a
    hand-built minimal catalog dict, rather than the real cc_2022.xml - this
    isolates validate.py's own comparison logic from catalog.py's loading,
    and lets a couple of conditions be triggered deterministically that the
    real catalog may not happen to exhibit."""

    def _run(self, root, cat):
        issues = []
        validate._stage1(root, cat, issues)
        return [i[0] for i in issues]

    def _component(self, id_, extended='false', hier_ids=(), dep_groups=(),
                    elements=()):
        comp = parser.E('component', id=id_, name='X', extended=extended)
        hier_el = parser.E('hierarchical_to')
        for h in hier_ids:
            hier_el.append(parser.E('comp_ref', id=h))
        comp.append(hier_el)
        deps_el = parser.E('dependencies')
        for group in dep_groups:
            dep_el = parser.E('dependency')
            alt_el = parser.E('alternatives')
            for a in group:
                alt_el.append(parser.E('comp_ref', id=a))
            dep_el.append(alt_el)
            deps_el.append(dep_el)
        comp.append(deps_el)
        elements_el = parser.E('elements')
        for el_id, el_type, el_text in elements:
            el = parser.E('element', id=el_id, type=el_type)
            el.append(parser.E('raw', el_text))
            elements_el.append(el)
        comp.append(elements_el)
        return comp

    def test_unknown_component_not_in_catalog(self):
        root = parser.E('cc_document')
        sfrs = parser.E('sfrs')
        sfrs.append(self._component('FAKE_ID.1'))
        root.append(sfrs)
        self.assertEqual(self._run(root, {}), ['UNKNOWN_COMPONENT'])

    def test_extended_component_skips_catalog_lookup_entirely(self):
        root = parser.E('cc_document')
        sfrs = parser.E('sfrs')
        sfrs.append(self._component('FAKE_EXT.1', extended='true'))
        root.append(sfrs)
        self.assertEqual(self._run(root, {}), [])  # empty catalog, but never consulted

    def test_hierarchical_mismatch_when_st_states_a_different_hierarchy(self):
        root = parser.E('cc_document')
        sfrs = parser.E('sfrs')
        sfrs.append(self._component('FIA_UAU.2', hier_ids=['WRONG_ID.1']))
        root.append(sfrs)
        cat = {'FIA_UAU.2': {'hierarchical_to': {'FIA_UAU.1'}, 'deps': [], 'elements': {}}}
        self.assertIn('HIERARCHICAL_MISMATCH', self._run(root, cat))

    def test_empty_element_raw_flagged(self):
        root = parser.E('cc_document')
        sfrs = parser.E('sfrs')
        sfrs.append(self._component('FIA_UID.2', elements=[('FIA_UID.2.1', None, None)]))
        root.append(sfrs)
        cat = {'FIA_UID.2': {'hierarchical_to': set(), 'deps': [], 'elements': {}}}
        self.assertIn('EMPTY_ELEMENT', self._run(root, cat))

    def test_element_type_mismatch_against_catalog(self):
        """The catalog's own tag (ae-developer/content/evaluator) determines
        its recorded type independently of the id's own D/C/E suffix
        letter, so a mismatch between the two is what this actually checks -
        constructed here since a real-world catalog inconsistency of this
        kind isn't something to depend on `ref/cc_2022.xml` happening to
        contain."""
        root = parser.E('cc_document')
        sars = parser.E('sars')
        sars.append(self._component('ADV_FSP.1', elements=[('ADV_FSP.1.1D', 'D', 'text')]))
        root.append(sars)
        cat = {'ADV_FSP.1': {'hierarchical_to': set(), 'deps': [],
                              'elements': {'ADV_FSP.1.1D': {'type': 'C', 'text': ''}}}}
        self.assertIn('ELEMENT_TYPE_MISMATCH', self._run(root, cat))

    def test_element_type_unknown_flagged(self):
        """Presently unreachable from real parser.py output (nothing ever
        sets an element's type attribute to the literal "unknown") - this
        pins validate.py's own handling of that value in isolation in case
        a future change (e.g. a new fallback path) makes it reachable."""
        root = parser.E('cc_document')
        sars = parser.E('sars')
        sars.append(self._component('ADV_FSP.1', elements=[('ADV_FSP.1.1X', 'unknown', 'text')]))
        root.append(sars)
        cat = {'ADV_FSP.1': {'hierarchical_to': set(), 'deps': [], 'elements': {}}}
        self.assertIn('ELEMENT_TYPE_MISMATCH', self._run(root, cat))


class TestExtendedComponents(unittest.TestCase):

    def test_parses_a_component_with_its_own_element(self):
        text = (
            'FCS_RBG_EXT.1 Random bit generation\n\n'
            'FCS_RBG_EXT.1.1 The TSF shall perform all random bit generation '
            'in accordance with [assignment: standard].\n'
        )
        families = parser.parse_extended_components(text)
        self.assertEqual(list(families), ['FCS_RBG_EXT'])
        comps = families['FCS_RBG_EXT']['components']
        self.assertEqual(comps[0]['id'], 'FCS_RBG_EXT.1')
        self.assertEqual(len(comps[0]['elements']), 1)

    def test_no_extended_components_yields_empty_families(self):
        self.assertEqual(parser.parse_extended_components('No extended components.\n'), {})


class TestGroupComponentsByClassFamily(unittest.TestCase):

    def test_groups_by_class_then_family_preserving_order(self):
        components = [
            {'id': 'FIA_UID.2'},
            {'id': 'FIA_UAU.2'},
            {'id': 'FDP_ACC.1'},
        ]
        grouped = parser.group_components_by_class_family(components)
        self.assertEqual(list(grouped.keys()), ['FIA', 'FDP'])
        self.assertEqual(list(grouped['FIA'].keys()), ['FIA_UID', 'FIA_UAU'])
        self.assertEqual(grouped['FDP']['FDP_ACC'][0]['id'], 'FDP_ACC.1')


class TestParseSfrSarElements(unittest.TestCase):

    def test_multiple_sfr_elements_with_operations(self):
        lines = [
            'FDP_ACF.1.1 The TSF shall enforce [assignment: policy].',
            'FDP_ACF.1.2 The TSF shall enforce the following rules: '
            '[assignment: rules].',
        ]
        elements = parser.parse_sfr_elements(lines, 0, len(lines))
        self.assertEqual([e['id'] for e in elements], ['FDP_ACF.1.1', 'FDP_ACF.1.2'])
        self.assertEqual(len(elements[0]['operations']), 1)

    def test_sar_element_type_comes_from_id_suffix_not_context_header(self):
        """SAR_TYPE_CONTEXT_RE ("Developer action elements:" etc.) is
        computed but never actually consulted - the D/C/E letter embedded
        directly in the element id is what determines `type`. Pinning this
        so nobody assumes the context header line matters."""
        lines = [
            'Evaluator action elements:',  # says "evaluator" (E)...
            'ADV_FSP.1.1D The developer shall provide a functional specification.',
        ]
        elements = parser.parse_sar_elements(lines, 0, len(lines))
        self.assertEqual(elements[0]['id'], 'ADV_FSP.1.1D')
        self.assertEqual(elements[0]['type'], 'D')  # ...but the id says D, and D wins

    def test_iteration_suffix_propagates_to_element_ids(self):
        lines = ['FCS_COP.1.1/Hash The TSF shall perform hashing.']
        elements = parser.parse_sfr_elements(lines, 0, len(lines))
        self.assertEqual(elements[0]['id'], 'FCS_COP.1.1/Hash')


class TestParseSfrComponent(unittest.TestCase):

    def test_combines_hierarchical_dependencies_elements_and_inclusion(self):
        lines = [
            'FAU_SAR.1 Audit review',
            '',
            'This SFR is optional, included only when local review is supported.',
            '',
            'Hierarchical to: No other components.',
            'Dependencies: FAU_GEN.1',
            '',
            'Application note: Some note.',
            '',
            'FAU_SAR.1.1 The TSF shall provide [assignment: authorised users].',
        ]
        comp = parser.parse_sfr_component(lines, 0, len(lines), kind='sfr')
        self.assertEqual(comp['id'], 'FAU_SAR.1')
        self.assertEqual(comp['name'], 'Audit review')
        self.assertEqual(comp['hierarchical_to'], [])
        self.assertEqual(comp['dependencies'], [{'alternatives': ['FAU_GEN.1'], 'unsatisfied': False}])
        self.assertEqual(comp['application_note'], 'Some note.')
        self.assertEqual(comp['inclusion'], 'optional')
        self.assertEqual(len(comp['elements']), 1)

    def test_sar_kind_is_always_mandatory_regardless_of_block_text(self):
        """`detect_inclusion` is only ever consulted for kind='sfr' -
        SAR components have no such optional/selection-based/objective
        concept in this schema."""
        lines = [
            'ADV_FSP.1 Basic functional specification',
            '',
            'This would say "optional SFR" if inclusion detection ran here.',
            '',
            'ADV_FSP.1.1D The developer shall provide a functional specification.',
        ]
        comp = parser.parse_sfr_component(lines, 0, len(lines), kind='sar')
        self.assertEqual(comp['inclusion'], 'mandatory')

    def test_iteration_label_extracted_from_header(self):
        lines = ['FCS_COP.1/Hash Cryptographic operation', '',
                 'FCS_COP.1.1/Hash The TSF shall perform hashing.']
        comp = parser.parse_sfr_component(lines, 0, len(lines), kind='sfr')
        self.assertEqual(comp['id'], 'FCS_COP.1')
        self.assertEqual(comp['iteration_label'], 'Hash')


def _minimal_comp(id_, name='X', iteration_label='', hierarchical_to=(),
                   dependencies=(), elements=(), inclusion='mandatory',
                   application_note=''):
    return {
        'id': id_, 'name': name, 'iteration_label': iteration_label,
        'hierarchical_to': list(hierarchical_to), 'dependencies': list(dependencies),
        'elements': list(elements), 'inclusion': inclusion,
        'application_note': application_note,
    }


class TestBuildXmlFunctions(unittest.TestCase):
    """The build_*_xml functions, fed hand-built dicts directly (bypassing
    the parse_* functions that normally produce them), to isolate "does the
    XML shape match the schema" from "was the text parsed correctly"."""

    def test_build_sfrs_xml_basic_shape(self):
        comp = _minimal_comp('FIA_UID.2', name='User identification',
                              elements=[{'id': 'FIA_UID.2.1', 'raw': 'text', 'operations': []}])
        classes = parser.group_components_by_class_family([comp])
        sfrs_el = parser.build_sfrs_xml(classes)
        comp_el = sfrs_el.find('.//component')
        self.assertEqual(comp_el.get('id'), 'FIA_UID.2')
        self.assertEqual(comp_el.get('extended'), 'false')
        self.assertEqual(len(comp_el.find('elements')), 1)
        self.assertEqual(comp_el.find('elements/element/raw').text, 'text')

    def test_build_sfrs_xml_marks_extended_ids(self):
        comp = _minimal_comp('FCS_RBG_EXT.1', name='RBG')
        classes = parser.group_components_by_class_family([comp])
        sfrs_el = parser.build_sfrs_xml(classes, extended_ids={'FCS_RBG_EXT.1'})
        comp_el = sfrs_el.find('.//component')
        self.assertEqual(comp_el.get('extended'), 'true')

    def test_build_sars_xml_element_has_type_attribute(self):
        comp = _minimal_comp('ADV_FSP.1', name='Basic functional specification',
                              elements=[{'id': 'ADV_FSP.1.1D', 'type': 'D', 'raw': 'text'}])
        classes = parser.group_components_by_class_family([comp])
        sars_el = parser.build_sars_xml(classes)
        el = sars_el.find('.//element')
        self.assertEqual(el.get('type'), 'D')
        self.assertEqual(el.get('id'), 'ADV_FSP.1.1D')

    def test_build_extended_components_xml_shape(self):
        comp = _minimal_comp('FCS_RBG_EXT.1', name='Random bit generation',
                              elements=[{'id': 'FCS_RBG_EXT.1.1', 'raw': 'text', 'operations': []}])
        families = {'FCS_RBG_EXT': {'class': 'FCS', 'components': [comp]}}
        ext_el, extended_ids = parser.build_extended_components_xml(families)
        self.assertEqual(extended_ids, {'FCS_RBG_EXT.1'})
        comp_el = ext_el.find('.//ext_component')
        self.assertEqual(comp_el.get('id'), 'FCS_RBG_EXT.1')
        # family_behaviour/component_levelling are always present but empty
        # (templates/GUIDE.md: their source text is never captured).
        fam_el = ext_el.find('.//ext_family')
        self.assertIsNotNone(fam_el.find('family_behaviour'))
        self.assertEqual(fam_el.find('family_behaviour').text, None)

    def test_build_introduction_xml_toe_version_blank_for_pp(self):
        doc_ref = {'identifier': '', 'title': 'Example PP', 'version': '1.0',
                   'date': '2026-01-01', 'author': '', 'sponsor': ''}
        st_el = parser.build_introduction_xml(doc_ref, 'ST', '')
        pp_el = parser.build_introduction_xml(doc_ref, 'PP', '')
        self.assertEqual(st_el.find('toe_overview/toe_version').text, '1.0')
        self.assertIsNone(pp_el.find('toe_overview/toe_version').text)


@unittest.skipUnless(CATALOG_PATH.exists(), f'{CATALOG_PATH} not present')
class TestApplyCatalogFallbackSarPath(unittest.TestCase):
    """apply_catalog_fallback's SAR branch specifically - the SFR branch is
    already covered by TestCatalogFallback above, but that class never
    exercises kind='sar' (D/C/E-typed elements)."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.load_catalog(str(CATALOG_PATH))

    def test_name_only_sar_component_gets_typed_elements_from_catalog(self):
        text = (
            "Test Doc\nVersion 1.0\n2026-01-01\n\n"
            "1. Introduction\nTest.\n\n"
            "2. Conformance Claims\nCC:2022 Part 2 conformant, Part 3 conformant, EAL1.\n\n"
            "3. Security Problem Definition\nT.X\nTest.\n\n"
            "4.1 Security Objectives for the TOE\nO.X\nTest.\n\n"
            "4.2 Security Objectives for the Operational Environment\nOE.X\nTest.\n\n"
            "5. Extended Components Definition\nNone.\n\n"
            "6. Security Functional Requirements\n\n"
            "FIA_UID.2 User identification before any action\n\n"
            "7. Security Assurance Requirements\n\n"
            "ADV_FSP.1 Basic functional specification\n\n"
            "8. Security Requirements Rationale\nO.X\nAddresses T.X.\n\n"
            "FIA_UID.2\nSatisfies O.X.\n\n"
            "9. TOE Summary Specification\nTest.\n"
        )
        root, _ = parser.parse_document(text, catalog=self.catalog)
        comp = root.find('.//sars//component')
        elements = comp.find('elements')
        self.assertEqual(elements.get('source'), 'catalog')
        self.assertGreater(len(elements), 0)
        types = {el.get('type') for el in elements.findall('element')}
        self.assertEqual(types, {'D', 'C', 'E'},
                          'ADV_FSP.1 has developer/content/evaluator elements')


if __name__ == '__main__':
    unittest.main()
