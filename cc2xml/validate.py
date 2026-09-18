"""
Validation per devNote.md's verification design:
  Stage 1 - structural check of parser output against the cc_2022.xml catalog
            (V1.1-V1.5), skipped entirely if no catalog is supplied.
  Stage 2 - self-consistency of the parser output alone (V2.1-V2.7), always run.

Produces a <validation_report> element appended to the parsed document root.
"""
from collections import Counter

from .parser import E


# ============================================================
# Stage 1 - cc_2022.xml catalog comparison
# ============================================================

def _satisfies_dependency(catalog, claimed_id, required_ids, _seen=None):
    """True if `claimed_id` satisfies one of `required_ids` - either directly,
    or by being hierarchically at-or-above one of them, checked transitively
    through the catalog's own hierarchical_to chains.

    ISO/IEC 15408-1:2026 §8.3 case (b) / 15408-2:2026 §7.4.3: "Components
    that are hierarchical to the identified component may also be used to
    satisfy the dependency." e.g. FDP_IFF.1 depends on FDP_IFC.1, but an ST
    that includes the hierarchically-higher FDP_IFC.2 instead has still
    satisfied that dependency - devnotes/todo/14 confirmed this previously
    raised a false DEPENDENCY_MISMATCH."""
    if claimed_id in required_ids:
        return True
    if _seen is None:
        _seen = set()
    if claimed_id in _seen:
        return False
    _seen.add(claimed_id)
    entry = catalog.get(claimed_id)
    if entry is None:
        return False
    return any(_satisfies_dependency(catalog, lower, required_ids, _seen)
               for lower in entry['hierarchical_to'])


def _stage1(root, catalog, issues):
    # V1.1 + V1.3: component id existence, hierarchical-to
    for comp in root.iter('component'):
        comp_id = comp.get('id')
        extended = comp.get('extended')
        if extended == 'true':
            continue  # V1.1 exception: extended components skip catalog lookup
        cat = catalog.get(comp_id.upper())
        if cat is None:
            issues.append(('UNKNOWN_COMPONENT', 'ERROR', comp_id, 'not found in cc_2022.xml catalog'))
            continue

        # V1.3 hierarchical-to
        parsed_hier = {c.get('id').upper() for c in comp.find('hierarchical_to') or []}
        if parsed_hier != cat['hierarchical_to']:
            issues.append(('HIERARCHICAL_MISMATCH', 'ERROR', comp_id,
                            f'parsed={sorted(parsed_hier)} catalog={sorted(cat["hierarchical_to"])}'))

        # V1.2 dependencies (subset-of-catalog-union check; an ST choosing one
        # alternative from a catalog OR-group is allowed per devNote.md)
        catalog_union = set()
        for g in cat['deps']:
            catalog_union |= g
        deps_el = comp.find('dependencies')
        if deps_el is not None:
            for dep in deps_el.findall('dependency'):
                if dep.get('unsatisfied') == 'true':
                    continue
                alt_ids = {r.get('id').upper() for r in dep.find('alternatives') or []}
                unmet = {a for a in alt_ids if not _satisfies_dependency(catalog, a, catalog_union)}
                if unmet:
                    issues.append(('DEPENDENCY_MISMATCH', 'ERROR', comp_id,
                                    f'{sorted(unmet)} not found among catalog dependencies {sorted(catalog_union)} '
                                    f'(directly or via hierarchical substitution)'))

        # V1.4 element raw non-empty
        for el in comp.iter('element'):
            raw = el.find('raw')
            if raw is None or not (raw.text or '').strip():
                issues.append(('EMPTY_ELEMENT', 'WARNING', el.get('id'), 'no raw text'))

        # V1.5 SAR element type match
        for el in comp.findall('.//element'):
            etype = el.get('type')
            if etype is None:
                continue  # SFR element, no type attribute
            cat_entry = cat['elements'].get(el.get('id').upper())
            cat_type = cat_entry['type'] if cat_entry else None
            if etype == 'unknown':
                issues.append(('ELEMENT_TYPE_MISMATCH', 'WARNING', el.get('id'), 'type could not be determined'))
            elif cat_type is not None and cat_type != etype:
                issues.append(('ELEMENT_TYPE_MISMATCH', 'ERROR', el.get('id'),
                                f'parsed={etype} catalog={cat_type}'))


# ============================================================
# Stage 2 - self-consistency
# ============================================================

def _stage2(root, issues):
    # V2.1 SPD completeness
    spd = root.find('spd')
    if spd is not None:
        n_threats = len(spd.find('threats'))
        n_assump = len(spd.find('assumptions'))
        n_osp = len(spd.find('osps'))
        if n_threats == 0 and n_assump == 0 and n_osp == 0:
            issues.append(('EMPTY_SPD', 'WARNING', 'spd', 'threats/assumptions/osps all empty'))

    # collect SPD ids
    spd_ids = set()
    if spd is not None:
        for tag in ('threat', 'assumption', 'osp'):
            for el in spd.iter(tag):
                spd_ids.add(el.get('id'))

    obj_ids = set()
    for tag in ('toe_objectives', 'env_objectives'):
        container = root.find(f'security_objectives/{tag}')
        if container is None:
            continue
        for obj in container.findall('objective'):
            obj_ids.add(obj.get('id'))

    rationale = root.find('rationale')

    # V2.2 objectives_rationale spd_ref validity (relaxed to WARNING - a
    # rationale legitimately referencing only some SPD elements is standard-
    # compliant, not an error). Objectives themselves carry no spd_refs
    # (traceability lives only in the rationale section), so this checks the
    # refs found there instead of on <objective> as before.
    if rationale is not None:
        for mapping in rationale.findall('.//objectives_rationale/mapping'):
            for r in mapping.findall('.//spd_ref'):
                if r.get('id') not in spd_ids:
                    issues.append(('DANGLING_SPD_REF', 'WARNING', mapping.get('objective_id'),
                                    f'unresolved spd_ref id={r.get("id")}'))

    # V2.3 SFR obj_refs -> objective dangling
    for comp in root.iter('component'):
        obj_refs = comp.find('obj_refs')
        if obj_refs is None:
            continue
        for r in obj_refs:
            if r.get('id') not in obj_ids:
                issues.append(('DANGLING_OBJ_REF', 'ERROR', comp.get('id'), f'unresolved obj_ref id={r.get("id")}'))

    # V2.4 hierarchy integrity: component id must share family id prefix,
    # family id must share class id prefix
    for sec_tag in ('sfrs', 'sars'):
        sec = root.find(sec_tag)
        if sec is None:
            continue
        for cls in sec.findall('class'):
            cls_id = cls.get('id')
            for fam in cls.findall('family'):
                fam_id = fam.get('id')
                if not fam_id.startswith(cls_id + '_'):
                    issues.append(('HIERARCHY_MISMATCH', 'ERROR', fam_id, f'family id does not share class prefix {cls_id}'))
                for comp in fam.findall('component'):
                    comp_id = comp.get('id')
                    if not comp_id.startswith(fam_id + '.'):
                        issues.append(('HIERARCHY_MISMATCH', 'ERROR', comp_id, f'component id does not share family prefix {fam_id}'))

    # V2.5 iteration uniqueness
    seen = Counter()
    for comp in root.iter('component'):
        key = (comp.get('id'), comp.get('iteration_label') or '')
        seen[key] += 1
    for (cid, it), count in seen.items():
        if count > 1:
            label = f'{cid}/{it}' if it else cid
            issues.append(('DUPLICATE_ITERATION', 'ERROR', label, f'appears {count} times'))

    # V2.6 operations format
    for el in root.iter('element'):
        ops = el.find('operations')
        if ops is None:
            continue
        labels = {op.get('label') for op in ops.findall('operation')}
        for op in ops.findall('operation'):
            optype = op.get('type')
            n_options = len(op.findall('option'))
            if optype == 'selection' and n_options == 0:
                issues.append(('MALFORMED_OPERATION', 'ERROR', el.get('id'),
                                f"selection operation {op.get('label')} has no options"))
            if optype == 'assignment' and n_options > 0:
                issues.append(('MALFORMED_OPERATION', 'ERROR', el.get('id'),
                                f"assignment operation {op.get('label')} unexpectedly has options"))
            nested_in = op.get('nested_in')
            if nested_in and nested_in not in labels:
                issues.append(('MALFORMED_OPERATION', 'ERROR', el.get('id'),
                                f"nested_in={nested_in} does not match any operation label in this element"))

    # V2.7 rationale coverage. No direct/derived distinction any more (see
    # devNote.md) - this simply runs whenever there's something to check
    # against; a document with no Rationale section at all just has every
    # objective/component come back unmapped, which is exactly what R11
    # ("missing section -> empty element") should surface as.
    obj_rat_ids = {m.get('objective_id') for m in rationale.findall('.//objectives_rationale/mapping')} if rationale is not None else set()
    for oid in obj_ids:
        if oid not in obj_rat_ids:
            issues.append(('UNMAPPED_OBJECTIVE', 'WARNING', oid, 'no mapping in objectives_rationale'))

    sfr_rat_ids = {m.get('comp_id') for m in rationale.findall('.//sfr_rationale/mapping')} if rationale is not None else set()
    sfrs_el = root.find('sfrs')
    for comp in (sfrs_el.iter('component') if sfrs_el is not None else []):
        cid = comp.get('id')
        full_id = cid + (f"/{comp.get('iteration_label')}" if comp.get('iteration_label') else '')
        if full_id not in sfr_rat_ids and cid not in sfr_rat_ids:
            issues.append(('UNMAPPED_SFR', 'WARNING', full_id, 'no mapping in sfr_rationale'))


def validate(root, catalog_path=None, catalog=None):
    """`catalog`, if given, is an already-`catalog.load_catalog()`-ed dict
    (avoids re-parsing the multi-MB cc_2022.xml a second time when the caller
    - e.g. cli.py, for parser.apply_catalog_fallback - already loaded it)."""
    issues = []
    stage1_status = 'skipped'
    if catalog is not None:
        _stage1(root, catalog, issues)
        stage1_status = 'ran'
    elif catalog_path:
        try:
            from . import catalog as catalog_mod
            catalog = catalog_mod.load_catalog(catalog_path)
            _stage1(root, catalog, issues)
            stage1_status = 'ran'
        except Exception as exc:  # pragma: no cover - defensive
            issues.append(('CATALOG_LOAD_ERROR', 'WARNING', catalog_path, str(exc)))
            stage1_status = 'error'

    _stage2(root, issues)

    stage1_errors = sum(1 for t, sev, loc, d in issues if sev == 'ERROR' and stage1_status == 'ran'
                         and t in {'UNKNOWN_COMPONENT', 'DEPENDENCY_MISMATCH', 'HIERARCHICAL_MISMATCH',
                                    'ELEMENT_TYPE_MISMATCH'})
    stage1_warnings = sum(1 for t, sev, loc, d in issues if sev == 'WARNING' and stage1_status == 'ran'
                           and t in {'EMPTY_ELEMENT', 'ELEMENT_TYPE_MISMATCH'})
    stage2_types = {'EMPTY_SPD', 'DANGLING_SPD_REF', 'DANGLING_OBJ_REF', 'HIERARCHY_MISMATCH',
                     'DUPLICATE_ITERATION', 'MALFORMED_OPERATION', 'UNMAPPED_OBJECTIVE', 'UNMAPPED_SFR'}
    stage2_errors = sum(1 for t, sev, loc, d in issues if sev == 'ERROR' and t in stage2_types)
    stage2_warnings = sum(1 for t, sev, loc, d in issues if sev == 'WARNING' and t in stage2_types)

    total_errors = sum(1 for t, sev, loc, d in issues if sev == 'ERROR')
    result = 'FAIL' if total_errors else ('WARN' if issues else 'PASS')

    report = E('validation_report')
    report.append(E('summary', None,
                     stage1=stage1_status,
                     stage1_errors=stage1_errors, stage1_warnings=stage1_warnings,
                     stage2_errors=stage2_errors, stage2_warnings=stage2_warnings,
                     result=result))
    issues_el = E('issues')
    for t, sev, loc, detail in issues:
        issues_el.append(E('issue', None, type=t, severity=sev, location=loc, detail=detail))
    report.append(issues_el)
    return report
