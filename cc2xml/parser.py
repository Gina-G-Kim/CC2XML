"""
Text -> XML parser for Common Criteria ST/PP documents.

Design basis (per devNote.md): ISO/IEC 15408-1/2/3:2022 and cc_2022.xml only.
Enterprise-authored ST documents (ANSSI-ST, CASA-ST, NIAP NDcPP-derived STs,
etc.) freely restyle the standard's structure and are NOT the design target -
this parser processes standard-shaped text only. Text outside the standard's
structure is preserved verbatim in <unparsed_fragment> rather than guessed
at. Real-world PDF-extraction quirks (rotated/scrambled table text, column
collapse, multi-page boilerplate, house-style fallbacks) are out of scope by
design: input is plain text/markdown authored directly, not PDF.
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict

# ============================================================
# Generic regex library
# ============================================================

TOC_DOTS_RE = re.compile(r'\.{2,}\s*\d+\s*$')
HEADER_NUM_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)\.?\s+(\S.*\S|\S)\s*$')

SPD_ID_RE = re.compile(
    r'^(T\.[A-Z][\w\-.]*|A\.[A-Z][\w\-.]*|P\.[A-Z][\w\-.]*|OSP\.[\w\-.]+)\s*[:\-–]?\s*(.*)$'
)
# R4: only O.NAME (TOE) / OE.NAME (environment) are recognized - no OT.
# variant, and the id charset is restricted to what the standard's own
# examples use (upper-case word chars, digits, '_', '-'). Anything else is
# left unmatched and falls through to <unparsed_fragment>.
OBJ_ID_RE = re.compile(
    r'^(OE\.[A-Z][A-Z0-9_\-]*|O\.[A-Z][A-Z0-9_\-]*)\s*[:\-–]?\s*(.*)$'
)

COMP_HEADER_RE = re.compile(
    r'^(?:(?P<pp>[A-Za-z][A-Za-z0-9]*):)?'
    r'(?P<class>[A-Z]{2,4})_(?P<fam>[A-Z0-9]+(?:_[A-Z0-9]+)*)\.(?P<num>\d+)'
    r'(?!\.\d)'
    r'(?:/(?P<iter>[A-Za-z0-9_\-]+))?'
    r'\s*[:\-–]?\s*'
    r'(?P<name>.*)$'
)

SFR_ELEM_HEADER_RE = re.compile(
    r'^(?:(?P<pp>[A-Za-z][A-Za-z0-9]*):)?'
    r'(?P<class>[A-Z]{2,4})_(?P<fam>[A-Z0-9]+(?:_[A-Z0-9]+)*)\.(?P<num>\d+)\.(?P<enum>\d+)'
    r'(?:/(?P<iter>[A-Za-z0-9_\-]+))?'
    r'\s*(?P<rest>.*)$'
)

SAR_ELEM_HEADER_RE = re.compile(
    r'^(?:(?P<pp>[A-Za-z][A-Za-z0-9]*):)?'
    r'(?P<class>[A-Z]{2,4})_(?P<fam>[A-Z0-9]+(?:_[A-Z0-9]+)*)\.(?P<num>\d+)\.(?P<enum>\d+)'
    r'(?P<sartype>[DCE])'
    r'(?:/(?P<iter>[A-Za-z0-9_\-]+))?'
    r'\s*(?P<rest>.*)$'
)

COMP_ID_TOKEN_RE = re.compile(r'\b[A-Z]{2,4}_[A-Z0-9]+(?:_[A-Z0-9]+)*\.\d+(?:/[A-Za-z0-9_\-]+)?\b')

# ASE_REQ.1.6C/ASE_REQ.2.7C: a real catalog dependency may be explicitly
# declared unsatisfied with a justification, instead of being met - see R7's
# _extract_unsatisfied_dependencies / devnotes/todo/15.
UNSATISFIED_DEP_RE = re.compile(
    r'^(?P<id>[A-Z]{2,4}_[A-Z0-9]+(?:_[A-Z0-9]+)*\.\d+(?:/[A-Za-z0-9_\-]+)?)\s*[-:.]?\s*'
    r'(?P<justification>(?:not\s+resolved|not\s+applicable|not\s+satisfied|is\s+not\s+met).*)$',
    re.IGNORECASE
)

FIELD_MARKER_RE = re.compile(
    r'^(Hierarchical\s+to\s*:|Dependencies\s*:|Application\s*[Nn]otes?\S*\s*:|'
    r'Management\s*:|Audit\s*:|Family\s+behaviou?r\s*:|'
    r'Component\s+levelling\s*:)',
    re.IGNORECASE
)

EAL_RE = re.compile(r'\bEAL\s*([1-7])\s*(\+|augmented)?\b', re.IGNORECASE)
CC_VERSION_RE = re.compile(
    r'(ISO/IEC\s*15408[:\s]*\d{4}[^\n,;.]*|CC[:\s]*2022\b|'
    r'CC\s*v(?:ersion)?\s*3\.1[^\n,;.]*|Common\s+Criteria\s+v(?:ersion)?\s*3\.1[^\n,;.]*)',
    re.IGNORECASE
)

CDATA_TAGS = {'raw', 'justification', 'completed_value', 'unparsed_fragment'}


# ============================================================
# Small XML build helpers
# ============================================================

def E(tag, text=None, **attrs):
    el = ET.Element(tag, {k: str(v) for k, v in attrs.items() if v is not None})
    if text:
        el.text = text
    return el


def _escape_attr(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


def _escape_text(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def serialize(root):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    _serialize_el(root, 0, lines)
    return '\n'.join(lines) + '\n'


def _serialize_el(el, depth, lines):
    indent = '  ' * depth
    attrs = ''.join(f' {k}="{_escape_attr(str(v))}"' for k, v in el.attrib.items())
    children = list(el)
    text = (el.text or '').strip('\n')
    has_text = bool(text.strip())
    if not children and not has_text:
        lines.append(f'{indent}<{el.tag}{attrs}/>')
        return
    if not children and has_text:
        if el.tag in CDATA_TAGS:
            safe_text = text.replace(']]>', ']]]]><![CDATA[>')
            lines.append(f'{indent}<{el.tag}{attrs}><![CDATA[{safe_text}]]></{el.tag}>')
        else:
            lines.append(f'{indent}<{el.tag}{attrs}>{_escape_text(text)}</{el.tag}>')
        return
    lines.append(f'{indent}<{el.tag}{attrs}>')
    for child in children:
        _serialize_el(child, depth + 1, lines)
    lines.append(f'{indent}</{el.tag}>')


# ============================================================
# R1 - document-level attributes
# ============================================================

def detect_doc_type(text):
    st = len(re.findall(r'Security\s+Target', text, re.IGNORECASE))
    pp = len(re.findall(r'Protection\s+Profile', text, re.IGNORECASE))
    return 'PP' if pp > st else 'ST'


def detect_eal(text):
    matches = EAL_RE.findall(text)
    if not matches:
        return 'unknown'
    normd = [f'EAL{num}+' if plus else f'EAL{num}' for num, plus in matches]
    return Counter(normd).most_common(1)[0][0]


def detect_cc_version(text):
    m = CC_VERSION_RE.search(text)
    return m.group(0).strip() if m else ''


# ============================================================
# R2 - top-level section boundary recognition
#
# Simple sequential, canonical-order, first-match search. The richness-
# scoring/embedded-fragment/component-line-exclusion machinery a real-PDF
# corpus needed (reused keyword phrases in unrelated subsections, content
# smeared across chapters by house style) has no reason to exist against a
# standard-shaped document: each of these chapter titles appears exactly
# once, in ISO/IEC 15408's own canonical order.
# ============================================================

SECTION_DEFS = [
    ('introduction', [r'\bIntroduction\b']),
    ('conformance_claims', [r'Conformance\s+Claims?']),
    ('spd', [r'Security\s+Problem\s+Definition']),
    ('toe_objectives', [r'Security\s+Objectives\s+for\s+the\s+TOE']),
    ('env_objectives', [r'Security\s+Objectives\s+for\s+the\s+(Operational\s+)?Environment']),
    ('extended_components', [r'Extended\s+Components?\s+Definition']),
    ('sfrs', [r'Security\s+Functional\s+Requirements']),
    ('sars', [r'Security\s+Assurance\s+Requirements']),
    ('rationale', [r'Objectives?\s+Rationale', r'Requirements?\s+Rationale', r'Security\s+Rationale']),
    ('toe_summary_spec', [r'TOE\s+Summary\s+Specification']),
]

_SECTION_DEFS_COMPILED = [
    (name, [re.compile(p, re.IGNORECASE) for p in patterns])
    for name, patterns in SECTION_DEFS
]


def _is_heading_line(line):
    s = line.strip()
    if not s or len(s) > 110:
        return False
    if TOC_DOTS_RE.search(s):
        return False
    return True


def find_section_spans(lines):
    """Sequential search in canonical CC document order. Returns
    {name: (start_line, end_line_exclusive)} ; missing sections omitted."""
    starts = OrderedDict()
    cursor = 0
    for name, compiled in _SECTION_DEFS_COMPILED:
        found = None
        # pass 1: numbered heading lines
        for i in range(cursor, len(lines)):
            line = lines[i]
            if not _is_heading_line(line):
                continue
            m = HEADER_NUM_RE.match(line)
            candidate = m.group(2) if m else None
            if candidate is None:
                continue
            if any(p.search(candidate) for p in compiled):
                found = i
                break
        # pass 2: relaxed, any short non-TOC line containing the keyword
        if found is None:
            for i in range(cursor, len(lines)):
                line = lines[i]
                if not _is_heading_line(line):
                    continue
                if any(p.search(line) for p in compiled):
                    found = i
                    break
        if found is not None:
            starts[name] = found
            cursor = found + 1

    names = list(starts.keys())
    spans = {}
    for idx, name in enumerate(names):
        start = starts[name]
        end = starts[names[idx + 1]] if idx + 1 < len(names) else len(lines)
        spans[name] = (start, end)
    return spans


def _span_text(lines, span):
    if span is None:
        return ''
    s, e = span
    return '\n'.join(lines[s:e])


# ============================================================
# Field-span extraction helpers (Hierarchical to / Dependencies / etc.)
# ============================================================

def _next_marker_index(lines, start, extra_stop_res=()):
    """Find the line index (relative, start inclusive search begins at start)
    of the next field marker / component / element header, to bound a
    multi-line field value."""
    for i in range(start, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        if UNSATISFIED_DEP_RE.match(line):
            # An id-led "not resolved/applicable/satisfied" justification
            # line (ASE_REQ.1.6C/ASE_REQ.2.7C) is not a new component header,
            # even though it starts with a valid id like one - devnotes/
            # todo/15 confirmed this line matching COMP_HEADER_RE below (any
            # id-prefixed line does, regardless of what follows) was silently
            # truncating the Dependencies field right before this line,
            # losing the justified dependency entirely.
            continue
        if FIELD_MARKER_RE.match(line):
            return i
        m = COMP_HEADER_RE.match(line)
        if m and m.group('name') and m.group('name').strip():
            # A bare id with nothing after it (e.g. a plain AND-required
            # dependency given its own line, "Dependencies: FDP_ACC.1\n
            # FMT_MSA.3") is never a real component header in this format -
            # find_component_blocks/parse_sfrs already require a non-empty
            # name for a header to become a real component, so treating a
            # name-less id line as a boundary here was a silent-data-loss
            # bug: it truncated whatever field was being scanned right
            # before that line, and (in find_component_blocks) could also
            # steal the *real* next component's own body into a component
            # that never survives parse_sfrs' own name filter, losing it
            # entirely rather than either attaching it correctly or raising
            # anything.
            return i
        if SFR_ELEM_HEADER_RE.match(line) or SAR_ELEM_HEADER_RE.match(line):
            return i
        for pat in extra_stop_res:
            if pat.match(line):
                return i
    return len(lines)


# ============================================================
# R3 - SPD block extraction
#
# Simplified per devNote.md: ASE_SPD.1 requires threat/assumption/OSP
# descriptions (with threat/agent/asset prose folded into the description
# itself) but defines no separate <assets>/<asset_refs> structure - that was
# an enterprise-house-style addition, not a standard requirement, and its
# exact tagging varied per document. A threat/assumption/OSP is just an id
# plus its full descriptive text.
# ============================================================

def parse_spd(spd_text):
    lines = spd_text.split('\n')
    starts = []
    for i, line in enumerate(lines):
        m = SPD_ID_RE.match(line.strip())
        if m:
            starts.append((i, m.group(1), m.group(2)))

    threats, assumptions, osps = [], [], []
    for idx, (i, ident, rest) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        block_lines = ([rest] if rest else []) + lines[i + 1:end]
        description = '\n'.join(block_lines).strip('\n').strip()
        entry = {'id': ident, 'description': description}
        if ident.startswith('T.'):
            threats.append(entry)
        elif ident.startswith('A.'):
            assumptions.append(entry)
        else:  # P. or OSP.
            osps.append(entry)
    return {'threats': threats, 'assumptions': assumptions, 'osps': osps}


def build_spd_xml(spd_data):
    spd_el = E('spd')
    threats_el = E('threats')
    for t in spd_data['threats']:
        threats_el.append(_build_spd_item('threat', t))
    spd_el.append(threats_el)

    assumptions_el = E('assumptions')
    for a in spd_data['assumptions']:
        assumptions_el.append(_build_spd_item('assumption', a))
    spd_el.append(assumptions_el)

    osps_el = E('osps')
    for o in spd_data['osps']:
        osps_el.append(_build_spd_item('osp', o))
    spd_el.append(osps_el)
    return spd_el


def _build_spd_item(tag, item):
    el = E(tag, id=item['id'])
    el.append(E('description', item['description']))
    return el


# ============================================================
# R4 - Security Objectives block extraction
#
# Simplified per devNote.md: no application_note field (not part of
# ASE_OBJ.2's content requirements), traceability to SPD elements lives only
# in the Rationale section's objectives_rationale, never inline here.
# ============================================================

def parse_objectives(section_text):
    lines = section_text.split('\n')
    starts = []
    for i, line in enumerate(lines):
        m = OBJ_ID_RE.match(line.strip())
        if m:
            starts.append((i, m.group(1), m.group(2)))

    objectives = []
    for idx, (i, ident, rest) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        block_lines = ([rest] if rest else []) + lines[i + 1:end]
        description = '\n'.join(block_lines).strip('\n').strip()
        objectives.append({'id': ident, 'description': description})
    return objectives


def build_objectives_xml(tag, objectives):
    container = E(tag)
    for o in objectives:
        obj_el = E('objective', id=o['id'])
        obj_el.append(E('description', o['description']))
        container.append(obj_el)
    return container


# ============================================================
# R5-R9 - SFR / SAR / Extended-Components component-block parsing
# (shared machinery: all three sections share the same textual shape)
# ============================================================

def find_component_blocks(lines):
    """Return list of (start, end, match) for component header lines."""
    blocks = []
    starts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if UNSATISFIED_DEP_RE.match(stripped):
            # An id-led "not resolved/applicable/satisfied" dependency
            # justification (devnotes/todo/15) is not a new component - same
            # false-positive as _next_marker_index's, but this is a separate
            # scan (segments the whole SFR/SAR section into per-component
            # spans up front), so it needs its own guard.
            continue
        m = COMP_HEADER_RE.match(stripped)
        if m and m.group('name') and m.group('name').strip():
            # A bare id with no name text after it (e.g. a plain
            # AND-required dependency on its own line) is never a real
            # component header - see the matching guard in
            # _next_marker_index for the full explanation. Excluding it
            # here is what actually matters: previously such a line still
            # became a segment boundary, silently absorbing the *real*
            # next component's entire body into a same-id-less block that
            # parse_sfrs' own named_blocks filter then discarded outright.
            starts.append((i, m))
    for idx, (i, m) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        blocks.append((i, end, m))
    return blocks


def parse_hierarchical_to(lines, start, end):
    for i in range(start, end):
        line = lines[i].strip()
        m = re.match(r'Hierarchical\s+to\s*:\s*(.*)', line, re.IGNORECASE)
        if m:
            span_end = _next_marker_index(lines, i + 1)
            span_end = min(span_end, end)
            text = m.group(1) + '\n' + '\n'.join(lines[i + 1:span_end])
            if re.search(r'no\s+other\s+components?', text, re.IGNORECASE):
                return []
            return sorted(set(COMP_ID_TOKEN_RE.findall(text)))
    return []


def _find_top_level_spans(text, open_ch='[', close_ch=']'):
    spans = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == open_ch:
            if depth == 0:
                start = i
            depth += 1
        elif ch == close_ch:
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    spans.append((start, i + 1))
                    start = None
    return spans


def _extract_unsatisfied_dependencies(text_lines):
    """R7 addendum (ASE_REQ.1.6C/ASE_REQ.2.7C, devnotes/todo/15): scan a
    Dependencies field's lines for an explicit "not resolved"/"not
    applicable"/"not satisfied"/"is not met" justification attached to one
    dependency id. Returns (deps, consumed_line_indices) - `deps` entries
    have `unsatisfied: True` plus a `justification`; `consumed_line_indices`
    marks which lines those came from, so the caller can blank them out
    before the normal satisfied-dependency scan runs (otherwise the same id
    would also be picked up there as an ordinary satisfied dependency)."""
    deps = []
    consumed = set()
    i = 0
    while i < len(text_lines):
        m = UNSATISFIED_DEP_RE.match(text_lines[i].strip())
        if not m:
            i += 1
            continue
        just_parts = [m.group('justification').strip()]
        consumed.add(i)
        j = i + 1
        while j < len(text_lines):
            nxt = text_lines[j].strip()
            if not nxt or COMP_ID_TOKEN_RE.match(nxt) or UNSATISFIED_DEP_RE.match(nxt):
                break
            just_parts.append(nxt)
            consumed.add(j)
            j += 1
        deps.append({
            'alternatives': [m.group('id').upper()],
            'unsatisfied': True,
            'justification': ' '.join(just_parts).strip(),
        })
        i = j
    return deps, consumed


def parse_dependencies(lines, start, end):
    """R7. Returns list of dependency dicts: {alternatives: [ids],
    unsatisfied: bool, justification: str (only present when unsatisfied)}."""
    for i in range(start, end):
        line = lines[i].strip()
        m = re.match(r'Dependencies\s*:\s*(.*)', line, re.IGNORECASE)
        if not m:
            continue
        span_end = _next_marker_index(lines, i + 1)
        span_end = min(span_end, end)
        text = (m.group(1) + '\n' + '\n'.join(lines[i + 1:span_end])).strip()
        if re.search(r'no\s+dependenc', text, re.IGNORECASE):
            return []

        text_lines = text.split('\n')
        deps, unsatisfied_consumed = _extract_unsatisfied_dependencies(text_lines)
        text = '\n'.join('' if li in unsatisfied_consumed else l for li, l in enumerate(text_lines))

        bracket_spans = _find_top_level_spans(text)
        consumed = []
        for (s, e) in bracket_spans:
            group_text = text[s + 1:e - 1]
            ids = COMP_ID_TOKEN_RE.findall(group_text)
            if ids:
                deps.append({'alternatives': sorted(set(ids)), 'unsatisfied': False})
            consumed.append((s, e))
        remainder = list(text)
        for (s, e) in consumed:
            for k in range(s, e):
                remainder[k] = ' '
        remainder_text = ''.join(remainder)

        for line2 in remainder_text.split('\n'):
            ids = COMP_ID_TOKEN_RE.findall(line2)
            if not ids:
                continue
            # Multiple ids on one line are separate AND-required dependencies
            # by convention (e.g. "Dependencies: FDP_ACC.1, FMT_SMR.1,
            # FMT_SMF.1" means all three) - only an explicit "or" between them
            # makes it a single OR-group of alternatives (the bracketed
            # "[FIA_UID.1 or FIA_UID.2]" form above is the unambiguous way to
            # express that; this plain-line "or" is a fallback for the same
            # intent written without brackets).
            if len(ids) > 1 and re.search(r'\bor\b', line2, re.IGNORECASE):
                deps.append({'alternatives': sorted(set(ids)), 'unsatisfied': False})
            else:
                for cid in ids:
                    deps.append({'alternatives': [cid], 'unsatisfied': False})
        return deps
    return []


def parse_application_note(lines, start, end):
    for i in range(start, end):
        line = lines[i].strip()
        m = re.match(r'Application\s*[Nn]ote\S*\s*:\s*(.*)', line, re.IGNORECASE)
        if m:
            span_end = _next_marker_index(lines, i + 1)
            span_end = min(span_end, end)
            text = (m.group(1) + '\n' + '\n'.join(lines[i + 1:span_end])).strip()
            return text
    return ''


OP_KEYWORD_RE = re.compile(r'^\[(assignment|selection)\s*:\s*(.*)\]$', re.DOTALL | re.IGNORECASE)


def parse_operations(raw_text, label_counter=None):
    if label_counter is None:
        label_counter = {'a': 0, 's': 0}
    ops = []
    for (s, e) in _find_top_level_spans(raw_text):
        block = raw_text[s:e].strip()
        m = OP_KEYWORD_RE.match(block)
        if not m:
            continue
        optype = m.group(1).lower()
        body = m.group(2)
        key = 'a' if optype == 'assignment' else 's'
        label_counter[key] += 1
        label = f'({key}{label_counter[key]})'
        if optype == 'assignment':
            ops.append({'type': 'assignment', 'label': label, 'options': [], 'nested_in': None})
        else:
            nested_spans = _find_top_level_spans(body)
            masked = list(body)
            for (ns, ne) in nested_spans:
                for k in range(ns, ne):
                    masked[k] = '\x00'
            # options are usually comma-separated, but a document whose
            # option text itself contains commas (e.g. "RFCs 4251, 4252, ...")
            # may use ';' as the top-level separator instead - split on either.
            raw_items = re.split(r'[,;]', ''.join(masked))
            options = []
            for it in raw_items:
                cleaned = it.replace('\x00', '').strip()
                if cleaned and not re.match(r'^[A-Za-z0-9]{1,3}\)$', cleaned):
                    options.append(cleaned)
            ops.append({'type': 'selection', 'label': label, 'options': options, 'nested_in': None})
            for (ns, ne) in nested_spans:
                nested_block = body[ns:ne].strip()
                nm = OP_KEYWORD_RE.match(nested_block)
                if nm and nm.group(1).lower() == 'assignment':
                    label_counter['a'] += 1
                    nlabel = f"(a{label_counter['a']})"
                    ops.append({'type': 'assignment', 'label': nlabel, 'options': [], 'nested_in': label})
    return ops


def parse_sfr_elements(lines, start, end):
    starts = []
    for i in range(start, end):
        m = SFR_ELEM_HEADER_RE.match(lines[i].strip())
        if m:
            starts.append((i, m))
    elements = []
    for idx, (i, m) in enumerate(starts):
        e_end = starts[idx + 1][0] if idx + 1 < len(starts) else end
        elem_id = f"{m.group('class')}_{m.group('fam')}.{m.group('num')}.{m.group('enum')}"
        if m.group('iter'):
            elem_id += f"/{m.group('iter')}"
        raw = (m.group('rest') + '\n' + '\n'.join(lines[i + 1:e_end])).strip()
        ops = parse_operations(raw)
        elements.append({'id': elem_id, 'raw': raw, 'operations': ops})
    return elements


SAR_TYPE_CONTEXT_RE = re.compile(
    r'(Developer\s+action|Content\s+and\s+presentation(?:\s+of\s+evidence)?|Evaluator\s+action)\s+elements?',
    re.IGNORECASE
)
SAR_TYPE_MAP = {'developer': 'D', 'content': 'C', 'evaluator': 'E'}


def parse_sar_elements(lines, start, end):
    starts = []
    context_type = None
    for i in range(start, end):
        s = lines[i].strip()
        cm = SAR_TYPE_CONTEXT_RE.search(s)
        if cm:
            first_word = cm.group(1).split()[0].lower()
            context_type = SAR_TYPE_MAP.get(first_word)
        m = SAR_ELEM_HEADER_RE.match(s)
        if m:
            starts.append((i, m))
    elements = []
    for idx, (i, m) in enumerate(starts):
        e_end = starts[idx + 1][0] if idx + 1 < len(starts) else end
        elem_id = f"{m.group('class')}_{m.group('fam')}.{m.group('num')}.{m.group('enum')}{m.group('sartype')}"
        if m.group('iter'):
            elem_id += f"/{m.group('iter')}"
        raw = (m.group('rest') + '\n' + '\n'.join(lines[i + 1:e_end])).strip()
        elements.append({'id': elem_id, 'type': m.group('sartype'), 'raw': raw})
    return elements


INCLUSION_RE = [
    (re.compile(r'selection-based|if\s+\[selection\]\s+is\s+chosen', re.IGNORECASE), 'selection_based'),
    (re.compile(r'\(O\)|optional\s+SFR|SFR\s+is\s+optional', re.IGNORECASE), 'optional'),
    (re.compile(r'\bobjective\b\s*SFR|\(objective\)|SFR\s*,?\s+is\s+an?\s+objective\b', re.IGNORECASE), 'objective'),
]


def detect_inclusion(block_text):
    for pat, label in INCLUSION_RE:
        if pat.search(block_text):
            return label
    return 'mandatory'


def parse_sfr_component(lines, start, end, kind='sfr'):
    m = COMP_HEADER_RE.match(lines[start].strip())
    comp_id = f"{m.group('class')}_{m.group('fam')}.{m.group('num')}"
    iteration = m.group('iter') or ''
    name = m.group('name').strip()
    block_text = '\n'.join(lines[start:end])

    hier = parse_hierarchical_to(lines, start, end)
    deps = parse_dependencies(lines, start, end)
    app_note = parse_application_note(lines, start, end)
    if kind == 'sar':
        elements = parse_sar_elements(lines, start, end)
    else:
        elements = parse_sfr_elements(lines, start, end)
    inclusion = detect_inclusion(block_text) if kind == 'sfr' else 'mandatory'

    return {
        'id': comp_id,
        'name': name,
        'iteration_label': iteration,
        'hierarchical_to': hier,
        'dependencies': deps,
        'application_note': app_note,
        'elements': elements,
        'inclusion': inclusion,
    }


def group_components_by_class_family(components):
    classes = OrderedDict()
    for c in components:
        m = re.match(r'([A-Z]{2,4})_([A-Z0-9]+(?:_[A-Z0-9]+)*)', c['id'])
        if not m:
            continue
        cls, fam = m.group(1), f"{m.group(1)}_{m.group(2)}"
        classes.setdefault(cls, OrderedDict())
        classes[cls].setdefault(fam, []).append(c)
    return classes


def parse_sfrs(section_text):
    lines = section_text.split('\n')
    blocks = find_component_blocks(lines)
    named_blocks = [(s, e, m) for (s, e, m) in blocks if m.group('name') and m.group('name').strip()]
    components = [parse_sfr_component(lines, s, e, kind='sfr') for (s, e, m) in named_blocks]
    return group_components_by_class_family(components)


def build_sfrs_xml(classes, extended_ids=None):
    extended_ids = extended_ids or set()
    sfrs_el = E('sfrs')
    for cls, families in classes.items():
        class_el = E('class', id=cls, name='')
        for fam, comps in families.items():
            fam_el = E('family', id=fam, name='')
            fam_el.append(E('user_notes'))
            fam_el.append(E('levelling_notes'))
            for c in comps:
                comp_el = E('component', id=c['id'], name=c['name'],
                            iteration_label=c['iteration_label'],
                            inclusion=c['inclusion'],
                            extended=str(c['id'] in extended_ids).lower())
                hier_el = E('hierarchical_to')
                for h in c['hierarchical_to']:
                    hier_el.append(E('comp_ref', id=h))
                comp_el.append(hier_el)

                deps_el = E('dependencies')
                for d in c['dependencies']:
                    dep_el = E('dependency', unsatisfied='true' if d['unsatisfied'] else None)
                    alt_el = E('alternatives')
                    for a in d['alternatives']:
                        alt_el.append(E('comp_ref', id=a))
                    dep_el.append(alt_el)
                    deps_el.append(dep_el)
                comp_el.append(deps_el)

                comp_el.append(E('management'))
                comp_el.append(E('audit_events'))

                elements_el = E('elements')
                for el in c['elements']:
                    element_el = E('element', id=el['id'])
                    element_el.append(E('raw', el['raw']))
                    ops_el = E('operations')
                    for op in el['operations']:
                        op_el = E('operation', type=op['type'], label=op['label'],
                                   nested_in=op['nested_in'])
                        for opt in op['options']:
                            op_el.append(E('option', opt))
                        op_el.append(E('completed_value'))
                        ops_el.append(op_el)
                    element_el.append(ops_el)
                    elements_el.append(element_el)
                comp_el.append(elements_el)

                comp_el.append(E('obj_refs'))
                comp_el.append(E('application_note', c['application_note'] or None))
                fam_el.append(comp_el)
            class_el.append(fam_el)
        sfrs_el.append(class_el)
    return sfrs_el


def parse_sars(section_text):
    lines = section_text.split('\n')
    blocks = find_component_blocks(lines)
    named_blocks = [(s, e, m) for (s, e, m) in blocks if m.group('name') and m.group('name').strip()]
    components = [parse_sfr_component(lines, s, e, kind='sar') for (s, e, m) in named_blocks]
    return group_components_by_class_family(components)


def build_sars_xml(classes):
    sars_el = E('sars')
    for cls, families in classes.items():
        class_el = E('class', id=cls, name='')
        for fam, comps in families.items():
            fam_el = E('family', id=fam, name='')
            for c in comps:
                comp_el = E('component', id=c['id'], name=c['name'], inclusion=c['inclusion'])
                hier_el = E('hierarchical_to')
                for h in c['hierarchical_to']:
                    hier_el.append(E('comp_ref', id=h))
                comp_el.append(hier_el)

                deps_el = E('dependencies')
                for d in c['dependencies']:
                    dep_el = E('dependency', unsatisfied='true' if d['unsatisfied'] else None)
                    alt_el = E('alternatives')
                    for a in d['alternatives']:
                        alt_el.append(E('comp_ref', id=a))
                    dep_el.append(alt_el)
                    deps_el.append(dep_el)
                comp_el.append(deps_el)

                elements_el = E('elements')
                for el in c['elements']:
                    element_el = E('element', id=el['id'], type=el['type'])
                    element_el.append(E('raw', el['raw']))
                    elements_el.append(element_el)
                comp_el.append(elements_el)
                fam_el.append(comp_el)
            class_el.append(fam_el)
        sars_el.append(class_el)
    return sars_el


# ============================================================
# cc_2022.xml catalog fallback - guarantee hierarchical_to/dependencies/
# element (description) text for every recognized real component
# ============================================================

def apply_catalog_fallback(root, catalog):
    """For every non-extended <component> the ST names (i.e. the parser
    already recognized its id+name), fill hierarchical_to/dependencies/
    elements from cc_2022.xml whenever the ST text left that field empty, so
    a real requirement's relationships and description are never silently
    missing just because the ST inherited a component unchanged from the
    base standard rather than restating it.

    Each field keeps whichever the ST text actually supplied untouched
    (source="st") - catalog data only fills a field that parsed empty
    (source="catalog"), it never overrides or merges with ST content. A
    catalog-filled element's text is the standard's own generic (still
    `[assignment: ...]`/`[selection: ...]`-bracketed) wording, not a
    TOE-specific completed value - it documents what's being claimed, not
    verbatim ST prose, which is why source="catalog" matters to a reader.

    Extended components have no catalog entry by construction (they're
    vendor-invented, not part of the standard) - `comp.get('extended')` is
    only ever set on <sfrs> components, so <sars>/extended <sfrs> components
    are naturally left untouched here; the ST is the only possible source for
    their hierarchical_to/dependencies/elements.
    """
    for section_tag in ('sfrs', 'sars'):
        section_el = root.find(section_tag)
        if section_el is None:
            continue
        is_sar = section_tag == 'sars'
        for comp in section_el.iter('component'):
            if comp.get('extended') == 'true':
                continue
            cat = catalog.get((comp.get('id') or '').upper())
            if cat is None:
                continue

            hier_el = comp.find('hierarchical_to')
            if hier_el is not None:
                if len(hier_el) == 0:
                    hier_el.set('source', 'catalog')
                    for h in sorted(cat['hierarchical_to']):
                        hier_el.append(E('comp_ref', id=h))
                else:
                    hier_el.set('source', 'st')

            deps_el = comp.find('dependencies')
            if deps_el is not None:
                if len(deps_el) == 0:
                    deps_el.set('source', 'catalog')
                    for group in cat['deps']:
                        dep_el = E('dependency')
                        alt_el = E('alternatives')
                        for a in sorted(group):
                            alt_el.append(E('comp_ref', id=a))
                        dep_el.append(alt_el)
                        deps_el.append(dep_el)
                else:
                    deps_el.set('source', 'st')

            elements_el = comp.find('elements')
            if elements_el is not None:
                if len(elements_el) == 0:
                    elements_el.set('source', 'catalog')
                    for elem_id, entry in cat['elements'].items():
                        element_el = E('element', id=elem_id,
                                        type=entry['type'] if is_sar else None)
                        element_el.append(E('raw', entry['text']))
                        if not is_sar:
                            ops_el = E('operations')
                            for op in parse_operations(entry['text']):
                                op_el = E('operation', type=op['type'], label=op['label'],
                                            nested_in=op['nested_in'])
                                for opt in op['options']:
                                    op_el.append(E('option', opt))
                                op_el.append(E('completed_value'))
                                ops_el.append(op_el)
                            element_el.append(ops_el)
                        elements_el.append(element_el)
                else:
                    elements_el.set('source', 'st')


# ============================================================
# Extended Components Definition (best-effort, reuses SFR component shape)
# ============================================================

def parse_extended_components(section_text):
    lines = section_text.split('\n')
    blocks = find_component_blocks(lines)
    families = OrderedDict()
    for (s, e, m) in blocks:
        if not m.group('name'):
            continue
        comp = parse_sfr_component(lines, s, e, kind='sfr')
        fam_id = re.match(r'([A-Z]{2,4}_[A-Z0-9]+(?:_[A-Z0-9]+)*)', comp['id']).group(1)
        cls_id = fam_id.split('_')[0]
        families.setdefault(fam_id, {'class': cls_id, 'components': []})
        families[fam_id]['components'].append(comp)
    return families


def build_extended_components_xml(families):
    ext_el = E('extended_components')
    for fam_id, data in families.items():
        fam_el = E('ext_family', id=fam_id, name='', **{'class': data['class']})
        fam_el.append(E('family_behaviour'))
        fam_el.append(E('component_levelling'))
        for c in data['components']:
            comp_el = E('ext_component', id=c['id'], name=c['name'])
            hier_el = E('hierarchical_to')
            for h in c['hierarchical_to']:
                hier_el.append(E('comp_ref', id=h))
            comp_el.append(hier_el)
            deps_el = E('dependencies')
            for d in c['dependencies']:
                dep_el = E('dependency')
                alt_el = E('alternatives')
                for a in d['alternatives']:
                    alt_el.append(E('comp_ref', id=a))
                dep_el.append(alt_el)
                deps_el.append(dep_el)
            comp_el.append(deps_el)
            comp_el.append(E('management'))
            comp_el.append(E('audit_events'))
            fam_el.append(comp_el)
        ext_el.append(fam_el)
    return ext_el, {c['id'] for data in families.values() for c in data['components']}


# ============================================================
# R10 - Rationale
#
# Simplified per devNote.md: ASE_OBJ.2/ASE_REQ.2 define rationale as
# narrative text (id, then a justification paragraph) - the X-matrix table
# form some enterprise STs use is a house convention, not a standard
# requirement, so table detection/reversal/raw-preservation is dropped
# entirely along with the direct/derived branching (a document either has a
# Rationale section or it doesn't; either way the schema shape is the same,
# empty where nothing was found).
# ============================================================

def parse_rationale(section_text):
    obj_id_re = re.compile(r'^(OE\.[A-Z][A-Z0-9_\-]*|O\.[A-Z][A-Z0-9_\-]*)\s*$')
    comp_id_re = re.compile(r'^[A-Z]{2,4}_[A-Z0-9]+(?:_[A-Z0-9]+)*\.\d+(?:/[A-Za-z0-9_\-]+)?\s*$')

    lines = section_text.split('\n')
    obj_mappings, sfr_mappings = [], []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        om = obj_id_re.match(line)
        cm = comp_id_re.match(line)
        if om:
            j = i + 1
            body = []
            while j < len(lines) and not obj_id_re.match(lines[j].strip()) and not comp_id_re.match(lines[j].strip()):
                body.append(lines[j])
                j += 1
            text = '\n'.join(body).strip()
            refs = sorted(set(re.findall(r'\b(?:T\.[\w\-.]+|A\.[\w\-.]+|P\.[\w\-.]+|OSP\.[\w\-.]+)\b', text)))
            obj_mappings.append({'objective_id': om.group(1), 'justification': text, 'spd_refs': refs})
            i = j
            continue
        if cm:
            j = i + 1
            body = []
            while j < len(lines) and not obj_id_re.match(lines[j].strip()) and not comp_id_re.match(lines[j].strip()):
                body.append(lines[j])
                j += 1
            text = '\n'.join(body).strip()
            refs = sorted(set(re.findall(r'\b(?:OE?\.[A-Z][A-Z0-9_\-]*)\b', text)))
            sfr_mappings.append({'comp_id': cm.group(0).strip(), 'justification': text, 'obj_refs': refs})
            i = j
            continue
        i += 1
    return {'objectives_rationale': obj_mappings, 'sfr_rationale': sfr_mappings}


def collect_dependency_justifications(*class_groups):
    """Flatten (comp_id, dep_id, justification) for every unsatisfied,
    justified dependency (R7's _extract_unsatisfied_dependencies) across the
    given class -> family -> [components] trees (sfrs and sars), for
    <dependency_rationale> - devnotes/todo/15."""
    out = []
    for classes in class_groups:
        for families in classes.values():
            for comps in families.values():
                for c in comps:
                    for d in c['dependencies']:
                        if d.get('unsatisfied') and d.get('justification'):
                            for dep_id in d['alternatives']:
                                out.append({'comp_id': c['id'], 'dep_id': dep_id,
                                            'justification': d['justification']})
    return out


def build_rationale_xml(rationale_data, dep_justifications=None):
    rat_el = E('rationale')

    obj_rat_el = E('objectives_rationale')
    for m in rationale_data['objectives_rationale']:
        map_el = E('mapping', objective_id=m['objective_id'])
        map_el.append(E('justification', m['justification']))
        refs_el = E('spd_refs')
        for r in m['spd_refs']:
            refs_el.append(E('spd_ref', id=r))
        map_el.append(refs_el)
        obj_rat_el.append(map_el)
    rat_el.append(obj_rat_el)

    sfr_rat_el = E('sfr_rationale')
    for m in rationale_data['sfr_rationale']:
        map_el = E('mapping', comp_id=m['comp_id'])
        map_el.append(E('justification', m['justification']))
        refs_el = E('obj_refs')
        for r in m['obj_refs']:
            refs_el.append(E('obj_ref', id=r))
        map_el.append(refs_el)
        sfr_rat_el.append(map_el)
    rat_el.append(sfr_rat_el)

    # ASE_REQ.1.6C/ASE_REQ.2.7C (devnotes/todo/15): populated from R7's
    # explicit "not resolved/applicable/satisfied" dependency justifications,
    # collected across sfrs/sars by collect_dependency_justifications.
    dep_rat_el = E('dependency_rationale')
    for d in (dep_justifications or []):
        map_el = E('mapping', comp_id=d['comp_id'], dep_id=d['dep_id'])
        map_el.append(E('satisfied_by', comp_id=''))
        map_el.append(E('justification', d['justification']))
        dep_rat_el.append(map_el)
    rat_el.append(dep_rat_el)
    return rat_el


# ============================================================
# Introduction / Conformance (best-effort, no explicit rule numbers in devNote)
# ============================================================

VERSION_RE = re.compile(r'\bVersion\s+([0-9][0-9A-Za-z.\-]*)', re.IGNORECASE)
DATE_RE = re.compile(
    r'([A-Z][a-z]+\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{2,4})'
)


def parse_doc_reference(cover_text):
    lines = [ln.strip() for ln in cover_text.split('\n') if ln.strip()]
    title_lines = []
    version, date = '', ''
    for ln in lines[:10]:
        if HEADER_NUM_RE.match(ln):
            break  # reached the first numbered chapter heading - cover page ends here
        vm = VERSION_RE.search(ln)
        dm = DATE_RE.search(ln)
        if vm and not version:
            version = vm.group(1)
        if dm and not date:
            date = dm.group(1)
        if not vm and not dm and len(title_lines) < 2 and not re.match(r'^(Certification-ID|Doc(ument)?\s*ID)', ln, re.IGNORECASE):
            title_lines.append(ln)
    return {
        'identifier': '',
        'title': ' '.join(title_lines),
        'version': version,
        'date': date,
        'author': '',
        'sponsor': '',
    }


def build_introduction_xml(doc_ref, doc_type, toe_overview_text):
    intro_el = E('introduction')
    ref_el = E('doc_reference')
    for k in ('identifier', 'title', 'version', 'date', 'author', 'sponsor'):
        ref_el.append(E(k, doc_ref.get(k) or None))
    intro_el.append(ref_el)

    overview_el = E('toe_overview')
    overview_el.append(E('toe_name', doc_ref.get('title') or None))
    overview_el.append(E('toe_version', doc_ref.get('version') if doc_type == 'ST' else None))
    overview_el.append(E('toe_type'))
    overview_el.append(E('description', toe_overview_text or None))
    intro_el.append(overview_el)
    return intro_el


def build_conformance_xml(text, cc_version):
    conf_el = E('conformance_claims')
    cc_conf_el = E('cc_conformance')
    cc_conf_el.append(E('cc_version', cc_version or None))
    part2 = 'extended' if re.search(r'Part\s*2\s*extended', text, re.IGNORECASE) else \
        ('strict' if re.search(r'Part\s*2\s*(conformant|strict)', text, re.IGNORECASE) else '')
    part3 = 'extended' if re.search(r'Part\s*3\s*extended', text, re.IGNORECASE) else \
        ('strict' if re.search(r'Part\s*3\s*(conformant|strict)', text, re.IGNORECASE) else '')
    cc_conf_el.append(E('part2_conformance', part2 or None))
    cc_conf_el.append(E('part3_conformance', part3 or None))
    conf_el.append(cc_conf_el)

    pp_claims_el = E('pp_claims')
    for pp_ref in sorted(set(re.findall(r'\bPP[-_][\w\-]+\b', text))):
        pp_claims_el.append(E('pp_claim', ref=pp_ref, conformance_type=''))
    conf_el.append(pp_claims_el)

    package_claims_el = E('package_claims')
    for num, plus in EAL_RE.findall(text)[:1]:
        package_claims_el.append(E('package_claim', ref=f'EAL{num}', augmented=str(bool(plus)).lower()))
    conf_el.append(package_claims_el)
    return conf_el


# ============================================================
# Top level
# ============================================================

def parse_document(text, catalog=None):
    lines = text.split('\n')
    spans = find_section_spans(lines)

    doc_type = detect_doc_type(text)
    eal = detect_eal(text)
    cc_version = detect_cc_version(text)

    root = E('cc_document', doc_type=doc_type, eal=eal, title='', version='', date='',
              cc_version=cc_version)

    # doc_reference (title/version/date) lives on the cover page, which
    # precedes the "Introduction" chapter heading found by find_section_spans -
    # never use intro_text for this, only the very start of the document.
    doc_ref = parse_doc_reference(text[:2000])
    root.set('title', doc_ref.get('title', ''))
    root.set('version', doc_ref.get('version', ''))
    root.set('date', doc_ref.get('date', ''))
    root.append(build_introduction_xml(doc_ref, doc_type, ''))

    conf_span = spans.get('conformance_claims')
    root.append(build_conformance_xml(_span_text(lines, conf_span), cc_version))

    spd_span = spans.get('spd')
    spd_data = parse_spd(_span_text(lines, spd_span))
    root.append(build_spd_xml(spd_data))

    obj_root = E('security_objectives')
    toe_obj_span = spans.get('toe_objectives')
    toe_objs = parse_objectives(_span_text(lines, toe_obj_span))
    obj_root.append(build_objectives_xml('toe_objectives', toe_objs))
    env_obj_span = spans.get('env_objectives')
    env_objs = parse_objectives(_span_text(lines, env_obj_span))
    obj_root.append(build_objectives_xml('env_objectives', env_objs))
    root.append(obj_root)

    ecd_span = spans.get('extended_components')
    ecd_families = parse_extended_components(_span_text(lines, ecd_span))
    ecd_el, extended_ids = build_extended_components_xml(ecd_families)
    root.append(ecd_el)

    sfr_span = spans.get('sfrs')
    sfr_classes = parse_sfrs(_span_text(lines, sfr_span))
    root.append(build_sfrs_xml(sfr_classes, extended_ids))

    sar_span = spans.get('sars')
    sar_classes = parse_sars(_span_text(lines, sar_span))
    root.append(build_sars_xml(sar_classes))

    rationale_span = spans.get('rationale')
    rationale_data = parse_rationale(_span_text(lines, rationale_span))
    dep_justifications = collect_dependency_justifications(sfr_classes, sar_classes)
    root.append(build_rationale_xml(rationale_data, dep_justifications))

    tss_span = spans.get('toe_summary_spec')
    tss_el = E('toe_summary_spec', doc_type_applies='ST')
    if doc_type == 'ST':
        tss_el.append(E('raw', _span_text(lines, tss_span).strip() or None))
    root.append(tss_el)

    root.append(E('unparsed_sections'))

    if catalog is not None:
        apply_catalog_fallback(root, catalog)

    return root, spans
