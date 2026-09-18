"""
End-to-end orchestration: plain text/markdown -> XML (parser.py) ->
validation_report (validate.py) -> output/<name>.xml

Input is authored directly as plain text or markdown (not PDF) - see
devNote.md: the design target is ISO/IEC 15408 + cc_2022.xml only, tested
against a hand-written, standard-shaped synthetic ST/PP, not real-world
vendor PDFs. No PDF-extraction step exists any more.

Usage:
    python3 -m cc2xml.cli tests/foo.md [more.md/.txt ...]
    python3 -m cc2xml.cli --all          # every .md/.txt file in tests/
"""
import argparse
import re
import sys
from pathlib import Path

from . import catalog as catalog_mod
from . import parser, validate

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / 'tests'
OUTPUT_DIR = ROOT / 'output'
CATALOG_PATH = ROOT / 'ref' / 'cc_2022.xml'


def process_text(path, catalog=None):
    """`catalog`, if given, is an already-loaded catalog.load_catalog() dict -
    used both to fill hierarchical_to/dependencies/elements the ST left empty
    (parser.apply_catalog_fallback, via parse_document) and for Stage-1
    validation, so cc_2022.xml is parsed once per run, not twice."""
    text = Path(path).read_text(encoding='utf-8')
    root, spans = parser.parse_document(text, catalog=catalog)
    report = validate.validate(root, catalog=catalog)
    root.append(report)
    return parser.serialize(root), report


def main(argv=None):
    ap = argparse.ArgumentParser(description='CC ST/PP text/markdown -> XML parser')
    ap.add_argument('files', nargs='*', help='.md/.txt file paths (default: tests dir)')
    ap.add_argument('--all', action='store_true', help='process every .md/.txt file in tests/')
    ap.add_argument('--no-catalog', action='store_true', help='skip cc_2022.xml Stage-1 validation')
    args = ap.parse_args(argv)

    if args.all or not args.files:
        paths = sorted(list(TEST_DIR.glob('*.md')) + list(TEST_DIR.glob('*.txt')))
    else:
        paths = [Path(p) for p in args.files]

    OUTPUT_DIR.mkdir(exist_ok=True)
    catalog = None
    if not args.no_catalog:
        try:
            catalog = catalog_mod.load_catalog(str(CATALOG_PATH))
        except Exception as exc:
            print(f'cc_2022.xml catalog load failed, continuing without it: {exc}', file=sys.stderr)

    results = []
    for path in paths:
        name = re.sub(r'\W+', '_', path.stem)
        out_path = OUTPUT_DIR / f'{name}.xml'
        try:
            xml_str, report = process_text(path, catalog)
            out_path.write_text(xml_str, encoding='utf-8')
            summary = report.find('summary').attrib
            results.append((path.name, summary['result'], summary))
            print(f'{path.name}: {summary["result"]}  -> {out_path}')
        except Exception as exc:
            results.append((path.name, 'ERROR', {'exception': str(exc)}))
            print(f'{path.name}: ERROR ({exc})', file=sys.stderr)

    return results


if __name__ == '__main__':
    main()
