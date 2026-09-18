"""
Loads cc_2022.xml (the CC Portal's machine-readable SFR/SAR catalog) into a
lookup index used by validate.py as Stage-1 ground truth.

devNote.md assumes a generic pp-template-ish shape and says explicitly to
verify the real root/tag names once the file is available and adjust XPath
accordingly (section 9, "cc_2022.xml을 받으면..."). The real CC:2022 catalog
uses lowercase ids and this shape (confirmed by inspection):

  <cc version="CC:2022" revision="0.9">
    <f-class id="fau" name="...">
      <f-family id="fau_arp" name="...">
        <f-component id="fau_arp.1" name="...">
          <fco-hierarchical>...</fco-hierarchical>
          <fco-dependencies>
            <fco-dependsoncomponent fcomponent="fau_gen.1"/>
            <fco-or>
              <fco-dependsoncomponent fcomponent="..."/>
              ...
            </fco-or>
          </fco-dependencies>
          <f-element id="fau_arp.1.1">...</f-element>
        </f-component>
      </f-family>
    </f-class>
    <a-class id="...">
      <a-family id="...">
        <a-component id="ace_ccl.1">
          <aco-dependencies>...</aco-dependencies>
          <ae-developer id="ace_ccl.1.1d">...</ae-developer>
          <ae-content id="ace_ccl.1.1c">...</ae-content>
          <ae-evaluator id="ace_ccl.1.1e">...</ae-evaluator>
        </a-component>
      </a-family>
    </a-class>
  </cc>

All ids are normalized to uppercase on load so they compare directly against
parser.py output (which preserves source-document casing, conventionally
uppercase per devNote.md section 8's "id 속성: 원문 표기 대소문자 그대로").
"""
import re
import xml.etree.ElementTree as ET

_SKIP_TAGS = {'selectionnotes', 'assignmentnotes', 'm-workunit'}


def _tag(el):
    return el.tag.rsplit('}', 1)[-1]


def _flatten_cc_text(el):
    """Flatten an <f-element>/<ae-developer>/<ae-content>/<ae-evaluator>'s
    mixed-content XML body into plain text, used as catalog-fallback
    `<raw>` text when an ST doesn't restate a component's own element text
    (see parser.apply_catalog_fallback).

    - <selection>/<assignment> become the same `[selection: ...]`/
      `[assignment: ...]` bracket convention parse_operations() already
      expects from real ST prose, so fallback text round-trips through the
      same operation-extraction path as ST-authored text.
    - <selectionnotes>/<assignmentnotes> (author guidance, not normative
      wording) and <m-workunit> (evaluator work-unit methodology nested
      inside most real <ae-evaluator> elements - not part of the SAR
      element's own required text) are dropped entirely.
    - <xref id="..."/> (a cross-reference to another component/element,
      seen even inside selection option text) renders as that id, upper-cased.
    """
    def walk(e):
        t = _tag(e)
        if t in _SKIP_TAGS:
            return ''
        if t == 'xref':
            return (e.get('id') or '').upper()
        if t == 'selection':
            items = [walk(c).strip() for c in e.findall('selectionitem')]
            items = [i for i in items if i]
            return f"[selection: {', '.join(items)}]"
        if t == 'assignment':
            items = [walk(c).strip() for c in e.findall('assignmentitem')]
            items = [i for i in items if i]
            return f"[assignment: {', '.join(items)}]"
        parts = [e.text or '']
        for c in e:
            parts.append(walk(c))
            parts.append(c.tail or '')
        return ''.join(parts)

    return re.sub(r'\s+', ' ', walk(el)).strip()


def _dep_groups(deps_el):
    """AND-of-(single-id-or-OR-group). Returns list of sets of comp ids."""
    groups = []
    if deps_el is None:
        return groups
    for child in deps_el:
        tag = child.tag.rsplit('}', 1)[-1]
        if tag == 'fco-or' or tag == 'aco-or':
            alt = set()
            for gc in child:
                cid = gc.get('fcomponent') or gc.get('acomponent')
                if cid:
                    alt.add(cid.upper())
            if alt:
                groups.append(alt)
        elif tag.endswith('dependsoncomponent'):
            cid = child.get('fcomponent') or child.get('acomponent')
            if cid:
                groups.append({cid.upper()})
    return groups


def _hier_ids(hier_el):
    ids = set()
    if hier_el is None:
        return ids
    for el in hier_el.iter():
        for attr in ('fcomponent', 'acomponent'):
            v = el.get(attr)
            if v:
                ids.add(v.upper())
    return ids


def load_catalog(path):
    tree = ET.parse(path)
    root = tree.getroot()
    catalog = {}

    for fclass in root.findall('f-class'):
        for ffam in fclass.findall('f-family'):
            for fcomp in ffam.findall('f-component'):
                cid = fcomp.get('id').upper()
                elements = {el.get('id').upper(): {'type': None, 'text': _flatten_cc_text(el)}
                            for el in fcomp.findall('f-element')}
                catalog[cid] = {
                    'kind': 'f',
                    'name': fcomp.get('name') or '',
                    'deps': _dep_groups(fcomp.find('fco-dependencies')),
                    'hierarchical_to': _hier_ids(fcomp.find('fco-hierarchical')),
                    'elements': elements,
                }

    for aclass in root.findall('a-class'):
        for afam in aclass.findall('a-family'):
            for acomp in afam.findall('a-component'):
                cid = acomp.get('id').upper()
                elements = {}
                for tag, t in (('ae-developer', 'D'), ('ae-content', 'C'), ('ae-evaluator', 'E')):
                    for ael in acomp.findall(tag):
                        elements[ael.get('id').upper()] = {'type': t, 'text': _flatten_cc_text(ael)}
                catalog[cid] = {
                    'kind': 'a',
                    'name': acomp.get('name') or '',
                    'deps': _dep_groups(acomp.find('aco-dependencies')),
                    'hierarchical_to': _hier_ids(acomp.find('aco-hierarchical')),
                    'elements': elements,
                }

    return catalog
